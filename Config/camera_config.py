# -*- coding: utf-8 -*-
"""
视频源配置：定义系统接哪几路摄像头
========================================
支持两种类型：
  usb  : USB 摄像头            -> 参数 index（设备索引，0/1/2...）
  rtsp : 网络摄像头(工厂老设备) -> 参数 url（rtsp:// 地址）

「tasks」字段是预留的【每路功能配置】：
  以后可以给不同摄像头配置不同功能，例如：
    "tasks": ["person_intrusion"]              # 人员闯入
    "tasks": ["person_intrusion", "fire"]      # 后续扩展的功能
  当前业务统一按 person_intrusion 处理，后续再按任务分发。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CameraConfig:
    """单路摄像头的配置描述"""
    id: str                                  # 摄像头编号（写日志用）
    type: str = "usb"                        # usb / rtsp
    index: int = 0                           # USB 设备索引
    url: str = ""                            # RTSP 地址
    resolution: Optional[tuple] = None       # 可选：设置分辨率 (w, h)
    reconnect_delay: float = 2.0             # RTSP 断流重连间隔（秒）
    max_retry: int = 3                       # RTSP 每次断流最多重连次数
    tasks: list = field(default_factory=lambda: ["person_intrusion"])  # 预留：该路启用的功能


# ==================== 摄像头列表（按需增删） ====================
CAMERAS: list[CameraConfig] = [
    CameraConfig(
        id="camera_0",
        type="usb",
        index=1,                 # USB 设备索引，打开失败可改 0/1/2
        resolution=(1280, 720),  # 可选：设置分辨率
        tasks=["person_intrusion"],
    ),
    # ---------- 示例：工厂旧摄像头走 RTSP（用的时候取消注释并填 url）----------
    # CameraConfig(
    #     id="camera_1",
    #     type="rtsp",
    #     url="rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101",
    #     reconnect_delay=2.0,
    #     max_retry=3,
    #     tasks=["person_intrusion"],
    # ),
]
