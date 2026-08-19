from ultralytics import YOLOWorld
import cv2

# ==========1、加载本地模型，初始化检测类别==========
model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")
model.set_classes(["person"])
conf_threshold = 0.35
frame_gap = 20  # 每20帧执行一次AI推理

# ==========2、打开视频文件==========
cap = cv2.VideoCapture("./Media/人2.mp4")
frame_index = 0
last_draw_frame = None  # 缓存上一次推理完成、带框带文字的画面

# ==========3、视频循环读取主循环==========
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_index += 1

    if frame_index % frame_gap == 0:
        # 执行AI推理
        results = model(frame, conf=conf_threshold)
        res = results[0]
        draw_frame = res.plot()

        count_person = 0
        for box in res.boxes:
            cls_name = res.names[int(box.cls[0])]
            if cls_name == "person":
                count_person += 1

        # 绘制左上角统计文字
        text_info_1 = f"person:{count_person}"
        cv2.putText(draw_frame, text_info_1, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if count_person > 0:
            cv2.putText(draw_frame, "WARNING: Person Detected!", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        last_draw_frame = draw_frame  # 更新缓存
    else:
        # 没有推理的帧：复用上次带框画面；无缓存则用原始帧
        if last_draw_frame is not None:
            draw_frame = last_draw_frame
        else:
            draw_frame = frame

    cv2.imshow("detect", draw_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()