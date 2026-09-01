# -*- coding: utf-8 -*-
"""无硬件验证 VideoSource 和 Detector 工厂的配置分发。"""
import os
import sys
import types

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# 工厂模块导入所需的最小占位依赖，不创建摄像头、不加载模型。
sys.modules["cv2"] = types.ModuleType("cv2")
sys.modules["numpy"] = types.ModuleType("numpy")

from Config.camera_config import CAMERAS
from Config.env_config import BoxEnvConfig, LaptopEnvConfig
from Detector import factory as detector_factory
from VideoSource.factory import create_sources

# 视频源工厂：按配置创建对象，但不调用 open()。
sources = create_sources(CAMERAS)
assert len(sources) == len(CAMERAS)
for config, source in zip(CAMERAS, sources):
    assert source.source_id == config.id
    assert source.source_type == config.type


class FakeTorchDetector:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeRknnDetector:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


# 替换最终模型构造器，只检查真实 create_detector() 的选择和传参。
detector_factory.TorchDetector = FakeTorchDetector
detector_factory.RknnDetector = FakeRknnDetector

laptop_cfg = LaptopEnvConfig()
laptop_detector = detector_factory.create_detector(laptop_cfg)
assert isinstance(laptop_detector, FakeTorchDetector)
assert laptop_detector.kwargs["model_path"] == laptop_cfg.model_path
assert laptop_detector.kwargs["conf_threshold"] == laptop_cfg.conf_threshold
assert laptop_detector.kwargs["class_names"] == laptop_cfg.class_names

box_cfg = BoxEnvConfig()
box_detector = detector_factory.create_detector(box_cfg)
assert isinstance(box_detector, FakeRknnDetector)
assert box_detector.kwargs["model_path"] == box_cfg.model_path
assert box_detector.kwargs["conf_threshold"] == box_cfg.conf_threshold
assert box_detector.kwargs["iou_threshold"] == box_cfg.iou_threshold
assert box_detector.kwargs["input_size"] == box_cfg.input_size
assert box_detector.kwargs["class_names"] == box_cfg.class_names

print("✅ 工厂无硬件测试通过：USB/RTSP 与 torch/RKNN 配置分发正常")
