# -*- coding: utf-8 -*-
"""
推理后端统一接口：所有后端（torch 笔记本 / rknn 盒子）都返回统一的 Detection。
业务代码只依赖本接口，不关心底层是 .pt 还是 .rknn。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Detection:
    """一次检测结果"""
    cls_id: int          # 类别 id
    cls_name: str        # 类别名，如 "person"
    conf: float          # 置信度 0~1
    box: tuple           # (x1, y1, x2, y2) 原始图像坐标


class BaseDetector(ABC):
    """所有推理后端的统一抽象接口"""

    @abstractmethod
    def detect(self, frame) -> list:
        """对一帧图像做目标检测，返回 Detection 列表"""
        ...

    @abstractmethod
    def release(self):
        """释放模型资源（必须是幂等的）"""
        ...
