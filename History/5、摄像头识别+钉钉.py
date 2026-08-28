from ultralytics import YOLOWorld
import cv2
import pyttsx3
import time
import threading
import requests
import json

# --------------------------配置区
DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"
model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")
model.set_classes(["person"])
conf_threshold = 0.35
frame_gap = 20
alert_cooldown = 10
# -----------------------------------------------------------------------------

is_speaking = False
last_alert_time = 0
alert_count = 0

def speak_alert():
    global is_speaking
    is_speaking = True
    # 每次播报新建引擎，规避pyttsx3锁死bug
    tts = pyttsx3.init()
    tts.say("警告，检测到人员闯入")
    tts.runAndWait()
    tts.stop()
    is_speaking = False

def send_ding_alert(count_num):
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
            headers={"Content-Type":"application/json;charset=utf-8"},
            timeout=5
        )
        print("【钉钉回执】", resp.text)
    except Exception as e:
        print("钉钉发送异常：", e)


cap = cv2.VideoCapture(0)
frame_index = 0
last_draw_frame = None
has_person = False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_index += 1

    if frame_index % frame_gap == 0:
        results = model(frame, conf=conf_threshold)
        res = results[0]
        draw_frame = res.plot()

        count_person = 0
        for box in res.boxes:
            cls_name = res.names[int(box.cls[0])]
            if cls_name == "person":
                count_person +=1

        has_person = count_person > 0

        cv2.putText(draw_frame, f"person:{count_person}", (20,40), cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
        if has_person:
            cv2.putText(draw_frame,"WARNING: Person Detected!",(20,80),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
        last_draw_frame = draw_frame
    else:
        if last_draw_frame is not None:
            draw_frame = last_draw_frame
        else:
            draw_frame = frame

    now = time.time()
    if has_person:
        if not is_speaking and (now - last_alert_time > alert_cooldown):
            alert_count += 1
            last_alert_time = now
            # 语音、钉钉同时触发，保证同频
            t = threading.Thread(target=speak_alert, daemon=True)
            t.start()
            send_ding_alert(alert_count)

    cv2.imshow("detect", draw_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()