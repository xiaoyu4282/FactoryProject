# -*- coding: utf-8 -*-
"""
RK3588 盒子环境推理后端：调用 .rknn 模型（RKNNLite / NPU）。
依赖包 rknnlite，只在实例化时才 import，避免笔记本环境缺包报错。
"""
import cv2
import numpy as np

from Detector.base_detector import BaseDetector, Detection


def yolov8_postprocess(outputs, img_w, img_h, input_size, conf_thres, iou_thres):
    """yolov8 rknn 后处理，适配 rknn 输出，返回 (boxes, scores, cls_ids)"""
    output0 = np.squeeze(outputs[0])
    boxes_list, scores_list, cls_list = [], [], []
    num_dets = output0.shape[-1]
    for i in range(num_dets):
        xc, yc, w, h = output0[0:4, i]
        conf_all = output0[4:, i]
        cls_id = int(np.argmax(conf_all))
        score = float(conf_all[cls_id])
        if score < conf_thres:
            continue
        # 坐标还原到原图
        x1 = (xc - w / 2) / input_size[0] * img_w
        y1 = (yc - h / 2) / input_size[1] * img_h
        x2 = (xc + w / 2) / input_size[0] * img_w
        y2 = (yc + h / 2) / input_size[1] * img_h
        boxes_list.append([x1, y1, x2, y2])
        scores_list.append(score)
        cls_list.append(cls_id)

    indices = cv2.dnn.NMSBoxes(boxes_list, scores_list, conf_thres, iou_thres)
    out_box, out_score, out_cls = [], [], []
    # 兼容 opencv 版本：indices 可能为 None
    if indices is not None and len(indices) > 0:
        for idx in indices.flatten():
            out_box.append(boxes_list[idx])
            out_score.append(scores_list[idx])
            out_cls.append(cls_list[idx])
    return out_box, out_score, out_cls


class RknnDetector(BaseDetector):
    def __init__(self, model_path, conf_threshold=0.35, iou_threshold=0.45,
                 input_size=(640, 640), class_names=None):
        from rknnlite.api import RKNNLite  # 延迟导入：笔记本环境没有 rknnlite 也不报错

        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_size = tuple(input_size)
        self.class_names = list(class_names or [])
        self._released = False

        self.rknn = RKNNLite()
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            raise Exception(f"RKNN模型加载失败 ret={ret}, 检查模型路径: {model_path}")
        ret = self.rknn.init_runtime()
        if ret != 0:
            raise Exception(f"RKNN runtime初始化失败 ret={ret}")
        print(f"[RknnDetector] ✅ 加载模型: {model_path} (NPU)")

    def detect(self, frame) -> list:
        if frame is None:
            return []
        img_h, img_w = frame.shape[:2]
        img_in = cv2.resize(frame, self.input_size)
        img_in = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB)
        img_in = np.expand_dims(img_in, axis=0)

        outputs = self.rknn.inference(inputs=[img_in])
        boxes, scores, clses = yolov8_postprocess(
            outputs, img_w, img_h, self.input_size,
            self.conf_threshold, self.iou_threshold)

        dets = []
        for box, score, cid in zip(boxes, scores, clses):
            cls_name = self.class_names[cid] if 0 <= cid < len(self.class_names) else str(cid)
            dets.append(Detection(cls_id=cid, cls_name=cls_name, conf=score, box=tuple(box)))
        return dets

    def release(self):
        if self._released:
            return
        self._released = True
        try:
            self.rknn.release()
        except Exception as e:
            print(f"[RknnDetector] release 异常: {e}")
