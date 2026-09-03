# -*- coding: utf-8 -*-
"""
工厂视觉检测系统 —— 业务主入口
========================================
设计目标：业务代码与「视频数据源」「推理后端」解耦，互不影响。

  视频数据源 : Config/camera_config.py 配置  ->  VideoSource/(USB/RTSP) 实现
  推理后端   : Config/env_config.py   配置  ->  Detector/(torch/rknn)  实现
  公共能力   : Tools/ 提供钉钉、日志、语音服务
  Web 页面   : Web/ 提供实时视频流 + 前端页面
  业务功能   : Features/ 按功能独立迭代

环境切换   : 改 Config/env_config.py 里的 ENV（"laptop"=笔记本大模型 / "box"=RK3588盒子NPU）
新增摄像头 : 在 Config/camera_config.py 的 CAMERAS 列表加一行即可，业务代码不用动
"""
import signal
import threading
import time

import cv2

from Config import camera_config, env_config
from Detector.factory import create_detector
from Tools.DingTalkService import DingTalkService
from Tools.LogServer import save_alert_log
from Tools.NotifyService import speak_alert
from VideoSource.factory import create_sources
from Web.frame_buffer import FrameBuffer
from Web.web_server import start_web_server

# ============================== 业务配置 ==============================
frame_gap = 20          # 每隔 N 帧做一次推理
alert_cooldown = 60     # 告警冷却（秒）

# ============================== 加载环境配置 ==============================
env_cfg = env_config.get_env_config()
print(f"当前环境: {env_cfg.env_name}  推理后端: {env_cfg.backend}  模型: {env_cfg.model_path}")
ding_talk_service = DingTalkService(env_cfg.dingding_webhook)

# ============================== 创建视频源（USB/RTSP） ==============================
sources = create_sources(camera_config.CAMERAS)
for src in sources:
    if not src.open():
        print(f"[{src.source_id}] ❌ 视频源打开失败: {src.source_type}")

if not sources:
    print("⚠️ 没有配置任何视频源，请检查 Config/camera_config.py")
    exit(1)

# ============================== 创建推理后端（torch/rknn） ==============================
detector = create_detector(env_cfg)

# ============================== 启动 Web 服务（实时视频页面） ==============================
frame_buffer = FrameBuffer()
if env_cfg.enable_web:
    start_web_server(
        frame_buffer,
        cam_ids=[src.source_id for src in sources],
        host=env_cfg.web_host,
        port=env_cfg.web_port,
    )

# ============================== 退出清理 ==============================
def cleanup_all():
    for src in sources:
        src.release()
    detector.release()
    if env_cfg.show_window and not env_cfg.enable_web:
        cv2.destroyAllWindows()

def sigint_handler(signum, frame):
    print("\n收到终止信号，准备退出...")
    cleanup_all()
    exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# ============================== 业务主循环（多路摄像头） ==============================
# 每路摄像头独立维护状态，互不干扰
cam_states = {
    src.source_id: {
        "frame_index": 0,
        "last_draw": None,
        "has_person": False,
        "count_person": 0,
        "max_conf": 0.0,
        "last_alert_time": 0,
        "alert_count": 0,
    }
    for src in sources
}

try:
    running = True
    while running:
        for src in sources:
            st = cam_states[src.source_id]

            ok, frame = src.read()
            if not ok or frame is None:
                continue

            st["frame_index"] += 1
            draw_frame = frame.copy()

            # ---------- 推理（每隔 frame_gap 帧一次） ----------
            if st["frame_index"] % frame_gap == 0:
                detections = detector.detect(frame)

                # 只统计目标类别（person 闯入检测）
                targets = [d for d in detections if d.cls_name == env_cfg.target_class]

                st["count_person"] = len(targets)
                st["max_conf"] = max((d.conf for d in targets), default=0.0)
                st["has_person"] = st["count_person"] > 0

                # 画框（用于告警截图）
                for d in targets:
                    x1, y1, x2, y2 = map(int, d.box)
                    cv2.rectangle(draw_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(draw_frame, f"{d.cls_name} {d.conf:.2f}", (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                cv2.putText(draw_frame, f"{src.source_id} person:{st['count_person']}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if st["has_person"]:
                    cv2.putText(draw_frame, "WARNING: Person Detected!", (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                st["last_draw"] = draw_frame
            else:
                if st["last_draw"] is not None:
                    draw_frame = st["last_draw"]

            # ---------- 推送到 Web（每帧都推，保证视频流畅；盒子环境同样可用） ----------
            if env_cfg.enable_web:
                frame_buffer.put(src.source_id, draw_frame)

            # ---------- 告警（每路独立冷却） ----------
            now = time.time()
            if st["has_person"] and (now - st["last_alert_time"] > alert_cooldown):
                st["alert_count"] += 1
                st["last_alert_time"] = now
                print(f"====[{src.source_id}] 触发第{st['alert_count']}次告警====")
                ding_talk_service.send_alert(st["alert_count"], src.source_id)

                # 笔记本专属：本地语音播报（子线程，不阻塞主循环；盒子环境自动跳过）
                if env_cfg.voice_alert:
                    threading.Thread(target=speak_alert, daemon=True).start()

                save_alert_log(
                    alert_seq=st["alert_count"],
                    alert_type="person_intrusion",
                    desc="检测到人员闯入",
                    person_cnt=st["count_person"],
                    conf=st["max_conf"],
                    cam_id=src.source_id,
                    frame_image=draw_frame,
                )

            # ---------- 笔记本专属：弹出视频窗口（盒子环境 / 启动 Web 后自动跳过） ----------
            if env_cfg.show_window and not env_cfg.enable_web:
                cv2.imshow(src.source_id, draw_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("收到按键 q，退出...")
                    running = False
                    break
finally:
    # 异常/正常退出都清理资源
    cleanup_all()
