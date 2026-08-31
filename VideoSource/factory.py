# -*- coding: utf-8 -*-
"""
数据源工厂：根据 Config/camera_config.py 里的配置，
创建对应的 USB / RTSP 数据源对象。
"""
from VideoSource.base_source import VideoSourceBase
from VideoSource.rtsp_source import RtspSource
from VideoSource.usb_source import UsbSource


def create_source(cam_cfg) -> VideoSourceBase:
    """根据单路摄像头配置对象，创建对应的数据源对象"""
    src_type = cam_cfg.type
    src_id = cam_cfg.id
    resolution = cam_cfg.resolution

    if src_type == "usb":
        return UsbSource(
            source_id=src_id,
            index=cam_cfg.index,
            resolution=resolution,
        )
    if src_type == "rtsp":
        if not cam_cfg.url:
            raise ValueError(f"[{src_id}] rtsp 类型必须配置 url")
        return RtspSource(
            source_id=src_id,
            url=cam_cfg.url,
            resolution=resolution,
            reconnect_delay=cam_cfg.reconnect_delay,
            max_retry=cam_cfg.max_retry,
        )
    raise ValueError(f"[{src_id}] 未知视频源类型: {src_type!r}，可选: usb / rtsp")


def create_sources(cameras) -> list:
    """根据摄像头配置列表，批量创建数据源"""
    return [create_source(cfg) for cfg in cameras]
