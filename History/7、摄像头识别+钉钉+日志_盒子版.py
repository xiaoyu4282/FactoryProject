from ultralytics import YOLOWorld
import cv2
import time
import requests
import json
import os
import csv
import signal
from datetime import datetime
# --------------------------配置区
DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"
model = YOLOWorld("./Weights/yolov8s-worldv2.pt")
model.set_classes(["person"])
conf_threshold = 0.35
frame_gap = 20
alert_cooldown = 10  # 告警冷却秒
# 日志截图存储配置
LOG_DIR = "./Logs"
IMAGE_DIR = os.path.join(LOG_DIR, "Images")
CSV_FILE = os.path.join(LOG_DIR, "LogInfoRecord.csv")
# -----------------------------------------------------------------------------
cap = None
def sigint_handler(signum, frame):
    """处理Ctrl+C退出，释放摄像头资源"""
    global cap
    print("\n收到终止信号，准备退出...")
    if cap is not None:
        cap.release()
    exit(0)

signal.signal(signal.SIGINT, sigint_handler)

# 创建文件夹
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# 初始化csv表头，不存在则新建
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "alert_seq", "alert_time", "alert_type", "desc",
            "person_cnt", "conf", "cam_id", "image_path"
        ])

def save_alert_log(alert_seq, alert_type, desc, person_cnt, conf, cam_id, frame_image):
    """保存告警截图 + 写入csv日志"""
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"alert_{alert_seq}_{now_str}.jpg"
    img_full_path = os.path.join(IMAGE_DIR, img_name)
    cv2.imwrite(img_full_path, frame_image)
    rel_img_path = os.path.join("Images", img_name)
    with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            alert_seq,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alert_type,
            desc,
            person_cnt,
            conf,
            cam_id,
            rel_img_path
        ])
    print(f"📝日志已保存，截图:{img_full_path}")

def send_ding_alert(count_num):
    """发送钉钉告警"""
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"告警：现场检测到人员闯入！第{count_num}次告警"
        }
    }
    try:
        resp = requests.post(
            DINGDING_WEBHOOK,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json;charset=utf-8"},
            timeout=5
        )
        print("【钉钉回执】", resp.text)
    except Exception as e:
        print("钉钉发送异常：", e)

# RK3588 USB摄像头初始化
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("索引0打开失败，尝试索引1")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("摄像头打开失败，程序退出")
        exit(1)

frame_index = 0
last_draw_frame = None
has_person = False
last_alert_time = 0
alert_count = 0
count_person = 0  # 初始化变量，修复作用域bug

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("读取帧失败，退出循环")
        break
    frame_index += 1
    draw_frame = frame.copy()

    if frame_index % frame_gap == 0:
        results = model(frame, conf=conf_threshold)
        res = results[0]
        draw_frame = res.plot()
        count_person = 0
        for box in res.boxes:
            cls_name = res.names[int(box.cls[0])]
            if cls_name == "person":
                count_person += 1
        has_person = count_person > 0
        cv2.putText(draw_frame, f"person:{count_person}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if has_person:
            cv2.putText(draw_frame, "WARNING: Person Detected!", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        last_draw_frame = draw_frame
    else:
        if last_draw_frame is not None:
            draw_frame = last_draw_frame

    now = time.time()
    # 冷却时间到，触发钉钉、存截图日志
    if has_person and (now - last_alert_time > alert_cooldown):
        alert_count += 1
        last_alert_time = now
        print(f"====触发第{alert_count}次告警====")
        send_ding_alert(alert_count)
        save_alert_log(
            alert_seq=alert_count,
            alert_type="person_intrusion",
            desc="检测到人员闯入",
            person_cnt=count_person,
            conf=conf_threshold,
            cam_id="camera_0",
            frame_image=draw_frame
        )

# 正常退出释放摄像头
cap.release()
