# -*- coding: utf-8 -*-
"""USB 摄像头数据源实现"""
import cv2

from VideoSource.base_source import VideoSourceBase


class UsbSource(VideoSourceBase):
    def __init__(self, source_id, index=0, resolution=None):
        self._source_id = source_id
        self.index = index
        self.resolution = tuple(resolution) if resolution else None
        self._cap = None

    # ---------------- 接口实现 ----------------
    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def source_type(self) -> str:
        return "usb"

    def open(self) -> bool:
        self.release()
        try:
            cap = cv2.VideoCapture(self.index)
            if self.resolution:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            if not cap.isOpened():
                cap.release()
                print(f"[{self.source_id}] ❌ USB(index={self.index}) 打开失败")
                return False
            self._cap = cap
            print(f"[{self.source_id}] ✅ USB(index={self.index}) 打开成功")
            return True
        except Exception as e:
            print(f"[{self.source_id}] ❌ USB 打开异常: {e}")
            self.release()
            return False

    def read(self):
        if not self.is_opened():
            return False, None
        try:
            return self._cap.read()
        except Exception as e:
            print(f"[{self.source_id}] ❌ USB 读取异常: {e}")
            return False, None

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def release(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
