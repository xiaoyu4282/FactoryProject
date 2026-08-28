# RK3588 预验证版本，无继电器，无TTS语音；USB摄像头
from ultralytics import YOLOWorld
import cv2
import time

# ==========配置项==========
# RK上使用rknn转换后的模型路径，这里你后面改成盒子上的路径
model_path = r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt"

conf_threshold = 0.35
frame_gap = 20
ENABLE_IMSHOW = True   # 无头盒子必须False，不弹出视频窗口
SAVE_ALERT_SCREENSHOT = True  # 开启告警截图

model = YOLOWorld(model_path)
model.set_classes(["person"])

cap = cv2.VideoCapture(0)
frame_index = 0
last_draw_frame = None
has_person = False
screenshot_index = 0  # 截图序号

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("摄像头读取结束")
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
            print(f"【ALERT】检测到人员，person={count_person}")

            # 保存告警截图，存到盒子本地当前目录
            if SAVE_ALERT_SCREENSHOT:
                screenshot_name = f"alert_{screenshot_index}_{int(time.time())}.jpg"
                cv2.imwrite(screenshot_name, draw_frame)
                print(f"保存告警截图:{screenshot_name}")
                screenshot_index += 1

        last_draw_frame = draw_frame
    else:
        if last_draw_frame is not None:
            draw_frame = last_draw_frame
        else:
            draw_frame = frame

    if ENABLE_IMSHOW:
        cv2.imshow("detect", draw_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if ENABLE_IMSHOW:
    cv2.destroyAllWindows()
cap.release()



# 部署盒子时候需要修改两行代码
# model_path = "./Weights/yolov8s-worldv2.rknn"
# SAVE_ALERT_SCREENSHOT = False  # 开启告警截图
# 转成.rknn模型格式



# 检测到人的推理帧才保存jpg
# SFTP获取形式获取图片：电脑和RK盒子必须在同一个局域网（同一个路由器），不在同一路由时需要做内网穿透


# 部署到盒子的流程
# 1、下载 MobaXterm 安装
# 2、获取盒子 ip。链接进入 MobaXterm
# 3、修改文件、转文件格式
# 4、通过 sftp 上传到盒子硬盘
# 5、SSH 终端（MobaXterm 黑窗口）执行 pip install，依赖安装到 RK 盒子磁盘
# 6、SSH 终端运行 python main.py，程序跑在 RK 盒子硬件上
# 5、从盒子拿截图，通过 MobaXterm 的 sftp 面板，把 jpg 拽回笔记本

# SSH：发指令给盒子，让盒子执行程序、装依赖、打印日志。
# SFTP：拷贝文件到盒子硬盘 / 把盒子文件拷回电脑。