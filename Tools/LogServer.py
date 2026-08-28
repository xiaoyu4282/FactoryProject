import os
import csv
from datetime import datetime
import cv2

# =========修改：改成相对路径，不要写死D盘========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FOLDER = os.path.join(BASE_DIR, "alert_log")
CSV_PATH = os.path.join(LOG_FOLDER, "alert_record.csv")
SNAP_FOLDER = os.path.join(LOG_FOLDER, "alert_snap")


# 初始化文件夹、csv表头
def init_log_env():
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
    if not os.path.exists(SNAP_FOLDER):
        os.makedirs(SNAP_FOLDER)
    # 创建表头
    if not os.path.exists(CSV_PATH):
        header = [
            "告警时间",
            "告警序号",
            "告警类型",
            "事件描述",
            "检测人员数量",
            "置信度",
            "摄像头编号",
            "截图文件相对路径"
        ]
        with open(CSV_PATH, mode="w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)


def save_alert_log(alert_seq:int, alert_type:str, desc:str, person_cnt:int, conf:float, cam_id:str, frame_image):
    """
    :param alert_seq: 告警序号
    :param alert_type: 告警类型 person_intrusion
    :param desc: 文字描述
    :param person_cnt: 检测到人数
    :param conf: 模型置信度
    :param cam_id: 摄像头编号 camera_0
    :param frame_image: opencv原始帧图像，用来保存截图
    :return:
    """
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    snap_filename = f"snap_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    snap_rel_path = os.path.join("alert_snap", snap_filename)
    snap_full_path = os.path.join(SNAP_FOLDER, snap_filename)

    # 保存截图
    cv2.imwrite(snap_full_path, frame_image)

    row = [
        time_str,
        alert_seq,
        alert_type,
        desc,
        person_cnt,
        round(conf,4),
        cam_id,
        snap_rel_path
    ]
    with open(CSV_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(row)

    print(f"[日志模块] 告警{alert_seq}已写入，截图：{snap_filename}")


# 关键：导入模块的时候自动初始化文件夹！！
init_log_env()