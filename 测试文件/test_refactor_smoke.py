# -*- coding: utf-8 -*-
"""重构后模块冒烟测试：验证 Config / VideoSource / Detector 三层能配合工作（不打开摄像头、不跑主循环）"""
import os
import sys

# 保证能 import 项目根目录下的包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Config import env_config, camera_config
from VideoSource.factory import create_sources
from Detector.factory import create_detector


def main():
    print("=" * 50)
    # 1. 环境配置
    env_cfg = env_config.get_env_config()
    print(f"[1] 环境配置 OK -> {env_cfg.env_name} / backend={env_cfg.backend} / model={env_cfg.model_path}")

    # 2. 数据源工厂（只创建对象，不 open，避免依赖摄像头硬件）
    sources = create_sources(camera_config.CAMERAS)
    print(f"[2] 数据源工厂 OK -> 共 {len(sources)} 路: " +
          ", ".join(f"{s.source_id}({s.source_type})" for s in sources))

    # 3. 推理后端工厂（加载模型）
    detector = create_detector(env_cfg)
    print(f"[3] 推理后端 OK -> {type(detector).__name__}")

    # 4. 用一张黑色测试图跑一次 detect（验证接口返回 Detection 列表）
    import numpy as np
    import cv2
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)  # 模拟一帧画面
    dets = detector.detect(frame)
    print(f"[4] detect() OK -> 返回 {len(dets)} 个 Detection（空场景预期为 0）")

    detector.release()
    print("=" * 50)
    print("✅ 全部模块配合正常")


if __name__ == "__main__":
    main()
