# -*- coding: utf-8 -*-
"""
笔记本环境推理后端：调用 .pt 大模型（ultralytics / PyTorch，GPU）。
依赖包 ultralytics，只在实例化时才 import，避免盒子环境缺包报错。
"""
from Detector.base_detector import BaseDetector, Detection


class TorchDetector(BaseDetector):
    def __init__(self, model_path, conf_threshold=0.35,
                 class_names=None, device=""):
        from ultralytics import YOLO  # 延迟导入：盒子环境没有 ultralytics 也不报错

        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.device = device or None

        # world 模型可以自定义类别（如只识别 person）
        if class_names:
            try:
                self.model.set_classes(class_names)
            except Exception as e:
                print(f"[TorchDetector] ⚠️ set_classes 不可用(非world模型): {e}")

        print(f"[TorchDetector] ✅ 加载模型: {model_path} (device={self.device or 'auto'})")

    def detect(self, frame) -> list:
        if frame is None:
            return []

        kwargs = {"conf": self.conf_threshold, "verbose": False}
        if self.device:
            kwargs["device"] = self.device

        results = self.model.predict(frame, **kwargs)
        if not results:
            return []

        dets = []
        res = results[0]
        names = getattr(res, "names", {}) or {}
        for b in (res.boxes or []):
            cls_id = int(b.cls[0])
            cls_name = names.get(cls_id, str(cls_id))
            x1, y1, x2, y2 = (float(v) for v in b.xyxy[0])
            conf = float(b.conf[0])
            dets.append(Detection(cls_id=cls_id, cls_name=cls_name, conf=conf,
                                  box=(x1, y1, x2, y2)))
        return dets

    def release(self):
        # ultralytics 无需显式释放；保留接口以保持一致
        pass
