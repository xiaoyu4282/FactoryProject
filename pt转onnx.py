from ultralytics import YOLO

pt_path = r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt"
model = YOLO(pt_path)
# 导出onnx，imgsz640，opset17
model.export(format="onnx", imgsz=640, opset=17)
