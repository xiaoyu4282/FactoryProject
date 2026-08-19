from ultralytics import YOLOWorld

model = YOLOWorld(r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt")
model.set_classes(["water spill","person"])
res = model("https://ultralytics.com/images/bus.jpg")
res[0].show()

# 识别图片中的人、标记之后展示图片