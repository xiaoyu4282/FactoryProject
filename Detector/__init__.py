# -*- coding: utf-8 -*-
"""Detector 包：推理后端实现（torch 笔记本 / rknn 盒子）"""
from Detector.base_detector import BaseDetector, Detection
from Detector.factory import create_detector

__all__ = ["BaseDetector", "Detection", "create_detector"]
