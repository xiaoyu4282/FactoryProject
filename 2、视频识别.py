from ultralytics import YOLOWorld
import cv2

# ==========1、加载本地模型，初始化检测类别==========
model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")

model.set_classes(["person"])
conf_threshold = 0.35
frame_gap = 20  # 每20帧抽一帧

# ==========2、打开视频文件==========
cap = cv2.VideoCapture("./Media/人1.mp4")
frame_index = 0

# ==========3、视频循环读取主循环==========
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_index += 1
    draw_frame = frame.copy()

    if frame_index % frame_gap == 0:
        # ==========4、推理，plot()自动画方框+标签+置信度==========
        results = model(frame, conf=conf_threshold)
        res = results[0]
        draw_frame = res.plot()  # 【核心】自动绘制彩色检测框、文字标签

        count_forklift = 0
        count_carton = 0

        # ==========5、解析结果统计数量==========
        for box in res.boxes:
            cls_name = res.names[int(box.cls[0])]
            if cls_name == "forklift":
                count_forklift += 1
            if cls_name == "carton":
                count_carton += 1

        # --------画面左上角绘制统计文字--------
        text_info_1 = f"forklift:{count_forklift}"
        text_info_2 = f"carton:{count_carton}"
        cv2.putText(draw_frame, text_info_1, (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0),2)
        cv2.putText(draw_frame, text_info_2, (20,80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0),2)

        # 检测到叉车，红色告警文字
        if count_forklift > 0:
            cv2.putText(draw_frame, "WARNING: Forklift Detected!", (20,130),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    # ==========6、显示画面==========
    cv2.imshow("detect", draw_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ==========7、释放资源==========
cap.release()
cv2.destroyAllWindows()