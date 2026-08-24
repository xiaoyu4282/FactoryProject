from ultralytics import YOLOWorld
import cv2
import pyttsx3
import time
import threading

model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")
model.set_classes(["person"])
conf_threshold = 0.35
frame_gap = 20  # 每20帧推理一次AI

tts_engine = pyttsx3.init()
is_speaking = False  # 语音是否正在播放锁

def speak_alert():
    global is_speaking
    is_speaking = True
    tts_engine.say("警告，检测到人员闯入")
    tts_engine.runAndWait()
    is_speaking = False


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
                count_person += 1

        has_person = count_person > 0

        text_info_1 = f"person:{count_person}"
        cv2.putText(draw_frame, text_info_1, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if has_person:
            cv2.putText(draw_frame, "WARNING: Person Detected!", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        last_draw_frame = draw_frame
    else:
        if last_draw_frame is not None:
            draw_frame = last_draw_frame
        else:
            draw_frame = frame

    # 检测到人，并且当前没有正在播报，就启动语音
    if has_person and not is_speaking:
        t = threading.Thread(target=speak_alert, daemon=True)
        t.start()

    cv2.imshow("detect", draw_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()




# 整体逻辑
# 触发条件：检测到人 has_person=True，并且语音没有正在播放 is_speaking=False，就立刻启动播报。
# 两次播报的间隔：等于语音播放本身的时长，大约 2 秒，没有额外设置的冷却时间。
# 人一直停留在画面：播报 2 秒 →播放结束锁释放 →立刻又触发下一次播报，循环往复。
# 播报过程中（2 秒内）：就算画面一直有人，也不会新开播报，避免同时多个语音。
# 人离开画面：不会打断正在播放的语音，播完这一遍；不再产生新播报。
# 人再次闯入：只要不在播报，马上播报。

# 注：
# 笔记本摄像头1s==30帧，部分摄像头1s=25帧