#这里把main.py最上方所有import原样复制过来

from rknnlite.api import RKNNLite

rknn = RKNNLite()
ret_load = rknn.load_rknn("./Weights/yolov8s-fp16.rknn")
print("load结果", ret_load)
ret_init = rknn.init_runtime()
print("init结果", ret_init)
rknn.release()
