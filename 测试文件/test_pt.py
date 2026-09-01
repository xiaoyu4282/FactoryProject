import os
import torch

# 手动重新敲一遍横杠，不要复制旧的字符串
pt_path = r"D:\Work\Project\FactoryProject\Weights\yolov8s-worldv2.pt"

print("文件是否存在：", os.path.exists(pt_path))
if os.path.exists(pt_path):
    print("文件大小bytes：", os.path.getsize(pt_path))
    ckpt = torch.load(pt_path, map_location="cpu", weights_only=False)
    print("✅pt文件读取成功")
else:
    print("❌文件找不到，请核对文件名")
