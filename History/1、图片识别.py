# 识别图片中的人

from ultralytics import YOLOWorld

model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")
model.set_classes(["water spill","person"])
res = model("https://ultralytics.com/images/bus.jpg")
res[0].show()

