# -*- coding: utf-8 -*-
"""
RTSP 网络摄像头数据源实现（兼容工厂老设备）
带断流自动重连：read() 读到失败帧会自动释放旧连接并重连，防止程序挂掉。
"""
import time

import cv2

from VideoSource.base_source import VideoSourceBase


class RtspSource(VideoSourceBase):
    def __init__(self, source_id, url, resolution=None,
                 reconnect_delay=2.0, max_retry=3):
        self._source_id = source_id
        self.url = url
        self.resolution = tuple(resolution) if resolution else None
        self.reconnect_delay = reconnect_delay
        self.max_retry = max_retry
        self._cap = None

    # ---------------- 接口实现 ----------------
    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def source_type(self) -> str:
        return "rtsp"

    def open(self) -> bool:
        self.release()
        try:
            cap = cv2.VideoCapture(self.url)
            if self.resolution:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            if not cap.isOpened():
                cap.release()
                print(f"[{self.source_id}] ❌ RTSP 连接失败: {self.url}")
                return False
            self._cap = cap
            print(f"[{self.source_id}] ✅ RTSP 连接成功: {self.url}")
            return True
        except Exception as e:
            print(f"[{self.source_id}] ❌ RTSP 打开异常: {e}")
            self.release()
            return False

    def read(self):
        if not self.is_opened():
            if not self._try_reconnect():
                return False, None
        try:
            ok, frame = self._cap.read()
        except Exception as e:
            print(f"[{self.source_id}] ❌ RTSP 读取异常: {e}")
            ok, frame = False, None

        if not ok or frame is None:
            # 断流 -> 释放旧连接并尝试重连
            print(f"[{self.source_id}] ⚠️ RTSP 断流，尝试重连...")
            self.release()
            self._try_reconnect()
            return False, None
        return True, frame

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def release(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    # ---------------- 内部：断流自动重连 ----------------
    def _try_reconnect(self) -> bool:
        """尝试重连，最多 max_retry 次，每次间隔 reconnect_delay 秒"""
        for attempt in range(1, self.max_retry + 1):
            print(f"[{self.source_id}] 🔄 重连中 第{attempt}/{self.max_retry}次...")
            time.sleep(self.reconnect_delay)
            if self.open():
                return True
        return False
