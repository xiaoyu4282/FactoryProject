# -*- coding: utf-8 -*-
"""告警截图和 CSV 日志服务。"""
import csv
import os
from datetime import datetime

import cv2


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
LOG_FOLDER = os.path.join(PROJECT_DIR, "Logs")
CSV_PATH = os.path.join(LOG_FOLDER, "LogInfoRecord.csv")
SNAP_FOLDER = os.path.join(LOG_FOLDER, "Images")


def init_log_env():
    """初始化日志目录和 CSV 表头，已有日志不会被覆盖。"""
    os.makedirs(LOG_FOLDER, exist_ok=True)
    os.makedirs(SNAP_FOLDER, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        header = [
            "alert_seq", "alert_time", "alert_type", "desc",
            "person_cnt", "conf", "cam_id", "image_path",
        ]
        with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as file:
            csv.writer(file).writerow(header)


def save_alert_log(alert_seq: int, alert_type: str, desc: str,
                   person_cnt: int, conf: float, cam_id: str, frame_image):
    """保存告警截图并向 CSV 追加一条日志。"""
    now = datetime.now()
    snap_filename = f"alert_{alert_seq}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    snap_rel_path = os.path.join("Images", snap_filename)
    snap_full_path = os.path.join(SNAP_FOLDER, snap_filename)

    cv2.imwrite(snap_full_path, frame_image)

    row = [
        alert_seq,
        now.strftime("%Y-%m-%d %H:%M:%S"),
        alert_type,
        desc,
        person_cnt,
        round(conf, 4),
        cam_id,
        snap_rel_path,
    ]
    with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as file:
        csv.writer(file).writerow(row)

    print(f"📝日志已保存，截图:{snap_full_path}")


init_log_env()