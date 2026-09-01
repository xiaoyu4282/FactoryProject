# -*- coding: utf-8 -*-
"""
视频源统一接口：所有数据源（USB/RTSP/未来扩展）都实现这个抽象类。
业务代码只依赖本接口，不关心底层是 USB 还是 RTSP —— 这就是解耦的关键。
"""
from abc import ABC, abstractmethod


class VideoSourceBase(ABC):
    """所有视频源的统一抽象接口"""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """摄像头编号，例如 camera_0，用于日志/告警标识"""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型，例如 'usb' / 'rtsp'"""
        ...

    @abstractmethod
    def open(self) -> bool:
        """打开数据源，成功返回 True"""
        ...

    @abstractmethod
    def read(self):
        """读取一帧，返回 (ok, frame)；
        ok=True 表示拿到有效帧，frame 为 BGR 图像；
        失败时 ok=False、frame=None（调用方应跳过本帧）"""
        ...

    @abstractmethod
    def is_opened(self) -> bool:
        """当前是否处于打开状态"""
        ...

    @abstractmethod
    def release(self):
        """释放资源（必须是幂等的，可重复调用）"""
        ...
