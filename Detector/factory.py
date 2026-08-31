# -*- coding: utf-8 -*-
"""
推理后端工厂：根据 Config/env_config.py 里的环境配置，创建对应的推理后端。
  backend == "torch" -> 笔记本 GPU（.pt）
  backend == "rknn"  -> RK3588 盒子 NPU（.rknn）
"""
from Detector.base_detector import BaseDetector
from Detector.rknn_detector import RknnDetector
from Detector.torch_detector import TorchDetector


def create_detector(env_cfg) -> BaseDetector:
    backend = getattr(env_cfg, "backend", "torch")

    if backend == "torch":
        return TorchDetector(
            model_path=env_cfg.model_path,
            conf_threshold=env_cfg.conf_threshold,
            class_names=getattr(env_cfg, "class_names", None),
            device=getattr(env_cfg, "device", ""),
        )
    if backend == "rknn":
        return RknnDetector(
            model_path=env_cfg.model_path,
            conf_threshold=env_cfg.conf_threshold,
            iou_threshold=env_cfg.iou_threshold,
            input_size=getattr(env_cfg, "input_size", (640, 640)),
            class_names=getattr(env_cfg, "class_names", None),
        )
    raise ValueError(f"未知推理后端: {backend!r}，可选: torch / rknn")
