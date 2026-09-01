# -*- coding: utf-8 -*-
"""
环境配置：切换运行环境 = 切换推理后端
========================================
  laptop : 笔记本开发环境，调用 .pt 大模型（PyTorch / GPU，ultralytics）
  box    : RK3588 盒子部署环境，调用 .rknn 模型（RKNNLite / NPU）

使用：只需要修改下方 ENV 变量，其余自动切换。
"""
from dataclasses import dataclass, field

# ==================== 在这里切换运行环境 ====================
ENV = "box"      # 可选: "laptop" | "box"
# ===========================================================

# ==================== 通用通知配置 ====================
DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"
# ======================================================


# ---------------- 笔记本环境（调用 .pt 大模型 / GPU）----------------
@dataclass
class LaptopEnvConfig:
    env_name: str = "laptop"
    backend: str = "torch"                      # 推理后端：torch
    model_path: str = "./Weights/yolov8s-worldv2.pt"
    conf_threshold: float = 0.35
    iou_threshold: float = 0.45
    input_size: tuple = (640, 640)
    class_names: list = field(default_factory=lambda: ["person"])  # world模型自定义类别
    device: str = ""                            # ultralytics 设备，""=自动(cuda优先)
    target_class: str = "person"                # 业务关注的类别
    dingding_webhook: str = DINGDING_WEBHOOK    # 钉钉机器人地址
    # ---------- 笔记本专属功能开关（盒子环境自动关闭） ----------
    show_window: bool = True                    # 弹出视频窗口
    voice_alert: bool = True                    # 本地语音播报
    # ---------- Web 服务 ----------
    enable_web: bool = True                     # 启动 Web 实时视频页面
    web_host: str = "0.0.0.0"                   # 监听地址（0.0.0.0=局域网可访问）
    web_port: int = 8000                        # 端口


# ---------------- RK3588 盒子环境（调用 .rknn 模型 / NPU）----------------
@dataclass
class BoxEnvConfig:
    env_name: str = "box"
    backend: str = "rknn"                       # 推理后端：rknn
    model_path: str = "./Weights/yolov8s-fp16.rknn"
    conf_threshold: float = 0.35
    iou_threshold: float = 0.45
    input_size: tuple = (640, 640)
    # yolov8s COCO 80 类
    class_names: list = field(default_factory=lambda: [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
        "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
        "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
        "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
        "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
        "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
        "hair drier", "toothbrush",
    ])
    device: str = ""
    target_class: str = "person"
    dingding_webhook: str = DINGDING_WEBHOOK    # 钉钉机器人地址
    # ---------- 盒子环境：关闭笔记本专属功能 ----------
    show_window: bool = False                   # 盒子无显示器，不弹窗口
    voice_alert: bool = False                   # 盒子不本地播报
    # ---------- Web 服务 ----------
    enable_web: bool = True                     # 启动 Web 实时视频页面（局域网查看/配置）
    web_host: str = "0.0.0.0"
    web_port: int = 8000


_ENV_CONFIGS = {
    "laptop": LaptopEnvConfig,
    "box": BoxEnvConfig,
}


def get_env_config():
    """返回当前环境对应的配置对象"""
    cfg_cls = _ENV_CONFIGS.get(ENV)
    if cfg_cls is None:
        raise ValueError(f"未知环境: {ENV!r}，可选: {list(_ENV_CONFIGS)}")
    return cfg_cls()
