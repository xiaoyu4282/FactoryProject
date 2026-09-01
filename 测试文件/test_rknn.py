from rknnlite.api import RKNNLite

rknn = RKNNLite()
ret_load = rknn.load_rknn("./Weights/yolov8s-fp16.rknn")
print("load_rknn结果", ret_load)

ret_init = rknn.init_runtime()
print("init_runtime结果", ret_init)

if ret_init == 0:
    print("✅NPU硬件初始化成功")
else:
    print("❌NPU初始化失败")

rknn.release()
