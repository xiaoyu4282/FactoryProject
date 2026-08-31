# -*- coding: utf-8 -*-
"""
工厂视觉检测系统 —— 业务主入口
========================================
设计目标：业务代码与「视频数据源」「推理后端」解耦，互不影响。

  视频数据源 : Config/camera_config.py 配置  ->  VideoSource/(USB/RTSP) 实现
  推理后端   : Config/env_config.py   配置  ->  Detector/(torch/rknn)  实现
  业务逻辑   : 本文件，只依赖上面两层提供的统一接口

环境切换   : 改 Config/env_config.py 里的 ENV（"laptop"=笔记本大模型 / "box"=RK3588盒子NPU）
新增摄像头 : 在 Config/camera_config.py 的 CAMERAS 列表加一行即可，业务代码不用动
"""
import csv
import json
import os
import signal
import threading
import time
from datetime import datetime

import cv2
import requests

from Config import camera_config, env_config
from Detector.factory import create_detector
from VideoSource.factory import create_sources

# ============================== 业务配置 ==============================
DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"

LOG_DIR = "./Logs"
IMAGE_DIR = os.path.join(LOG_DIR, "Images")
CSV_FILE = os.path.join(LOG_DIR, "LogInfoRecord.csv")

frame_gap = 20          # 每隔 N 帧做一次推理
alert_cooldown = 10     # 告警冷却（秒）

# ============================== 加载环境配置 ==============================
env_cfg = env_config.get_env_config()
print(f"当前环境: {env_cfg.env_name}  推理后端: {env_cfg.backend}  模型: {env_cfg.model_path}")

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

# ============================== 退出清理 ==============================
def cleanup_all():
    for src in sources:
        src.release()
    detector.release()
    if env_cfg.show_window:
        cv2.destroyAllWindows()

def sigint_handler(signum, frame):
    print("\n收到终止信号，准备退出...")
    cleanup_all()
    exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# ============================== 日志初始化 ==============================
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow([
            "alert_seq", "alert_time", "alert_type", "desc",
            "person_cnt", "conf", "cam_id", "image_path"
        ])

def save_alert_log(alert_seq, alert_type, desc, person_cnt, conf, cam_id, frame_image):
    """保存告警截图 + 写入 csv 日志"""
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"alert_{alert_seq}_{now_str}.jpg"
    img_full_path = os.path.join(IMAGE_DIR, img_name)
    cv2.imwrite(img_full_path, frame_image)
    rel_img_path = os.path.join("Images", img_name)
    with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow([
            alert_seq,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alert_type,
            desc,
            person_cnt,
            round(conf, 4),
            cam_id,
            rel_img_path
        ])
    print(f"📝日志已保存，截图:{img_full_path}")

def send_ding_alert(count_num, cam_id="camera_0"):
    """发送钉钉告警"""
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"告警[{cam_id}]: Person intrusion detected! No.{count_num}"
        }
    }
    try:
        resp = requests.post(
            DINGDING_WEBHOOK,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=5
        )
        print("【钉钉回执】", resp.text)
    except Exception as e:
        print("钉钉发送异常：", e)

def speak_alert():
    """本地语音播报（仅笔记本使用；惰性导入 pyttsx3，盒子环境不会缺包报错）"""
    try:
        import pyttsx3
        tts = pyttsx3.init()
        tts.say("警告，检测到人员闯入")
        tts.runAndWait()
        tts.stop()
    except Exception as e:
        print("语音播报异常：", e)

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

            # ---------- 告警（每路独立冷却） ----------
            now = time.time()
            if st["has_person"] and (now - st["last_alert_time"] > alert_cooldown):
                st["alert_count"] += 1
                st["last_alert_time"] = now
                print(f"====[{src.source_id}] 触发第{st['alert_count']}次告警====")
                send_ding_alert(st["alert_count"], src.source_id)

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

            # ---------- 笔记本专属：弹出视频窗口（盒子环境自动跳过） ----------
            if env_cfg.show_window:
                cv2.imshow(src.source_id, draw_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("收到按键 q，退出...")
                    running = False
                    break
finally:
    # 异常/正常退出都清理资源
    cleanup_all()
