# -*- coding: utf-8 -*-
"""
共享帧缓冲：主循环(生产者)写入每路摄像头最新画面，Web(消费者)读取并转成 MJPEG 流。
线程安全，只保留每路摄像头的最新一帧。
"""
import threading


class FrameBuffer:
    """每路摄像头只保留最新一帧的线程安全缓冲，带序号以支持"只发新帧"。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._frames = {}
        self._seqs = {}

    def put(self, cam_id: str, frame):
        """写入某路摄像头的最新帧（覆盖旧帧），序号 +1。"""
        with self._lock:
            self._frames[cam_id] = frame
            self._seqs[cam_id] = self._seqs.get(cam_id, 0) + 1

    def get(self, cam_id: str):
        """返回 (frame, seq)；该路还没有帧时返回 (None, 0)。"""
        with self._lock:
            return self._frames.get(cam_id), self._seqs.get(cam_id, 0)

    def list_ids(self):
        """返回当前已有帧的摄像头编号列表。"""
        with self._lock:
            return list(self._frames.keys())
