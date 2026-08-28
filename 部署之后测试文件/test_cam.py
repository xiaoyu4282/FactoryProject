import cv2

# 优先试0，如果黑屏打不开换成1还不行换成2
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌摄像头打开失败")
else:
    print("✅摄像头打开成功")
    ret, frame = cap.read()
    if ret:
        print("✅成功读到图像帧")
        cv2.imwrite("./test_cam.jpg", frame)
        print("✅截图保存 test_cam.jpg")
    else:
        print("❌读取画面帧失败")

cap.release()
