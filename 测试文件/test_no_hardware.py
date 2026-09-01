# -*- coding: utf-8 -*-
"""无模型、无摄像头集成测试：验证 main.py 的模块连接和一次告警流程。"""
import json
import os
import runpy
import sys
import types

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

records = {
    "detected": 0,
    "detector_released": 0,
    "source_released": 0,
    "ding": [],
    "logs": [],
    "voice": 0,
}


class FakeFrame:
    def copy(self):
        return FakeFrame()


class FakeSource:
    source_id = "camera_test"
    source_type = "usb"

    def __init__(self):
        self.read_count = 0

    def open(self):
        return True

    def read(self):
        self.read_count += 1
        return True, FakeFrame()

    def release(self):
        records["source_released"] += 1


class FakeDetector:
    def detect(self, frame):
        records["detected"] += 1
        return [types.SimpleNamespace(
            cls_name="person",
            conf=0.90,
            box=(10, 20, 100, 200),
        )]

    def release(self):
        records["detector_released"] += 1


class FakeDingTalkService:
    def __init__(self, webhook_url):
        assert webhook_url

    def send_alert(self, count_num, cam_id="camera_0"):
        records["ding"].append((count_num, cam_id))


def fake_save_alert_log(**kwargs):
    records["logs"].append(kwargs)


def fake_speak_alert():
    records["voice"] += 1


# main.py 依赖的 OpenCV 最小接口；不会打开真实窗口或摄像头。
cv2 = types.ModuleType("cv2")
cv2.FONT_HERSHEY_SIMPLEX = 0
cv2.rectangle = lambda *args, **kwargs: None
cv2.putText = lambda *args, **kwargs: None
cv2.imshow = lambda *args, **kwargs: None
cv2.destroyAllWindows = lambda: None
wait_count = {"value": 0}


def fake_wait_key(delay):
    wait_count["value"] += 1
    return ord("q") if wait_count["value"] >= 20 else -1


cv2.waitKey = fake_wait_key
sys.modules["cv2"] = cv2

# 替换需要真实模型、摄像头或外部服务的模块，但保留 main.py 的真实控制流程。
detector_factory = types.ModuleType("Detector.factory")
detector_factory.create_detector = lambda env_cfg: FakeDetector()
sys.modules["Detector.factory"] = detector_factory

video_factory = types.ModuleType("VideoSource.factory")
video_factory.create_sources = lambda cameras: [FakeSource()]
sys.modules["VideoSource.factory"] = video_factory

ding_module = types.ModuleType("Tools.DingTalkService")
ding_module.DingTalkService = FakeDingTalkService
sys.modules["Tools.DingTalkService"] = ding_module

log_module = types.ModuleType("Tools.LogServer")
log_module.save_alert_log = fake_save_alert_log
sys.modules["Tools.LogServer"] = log_module

notify_module = types.ModuleType("Tools.NotifyService")
notify_module.speak_alert = fake_speak_alert
sys.modules["Tools.NotifyService"] = notify_module

runpy.run_path(os.path.join(PROJECT_DIR, "main.py"), run_name="__main__")

assert records["detected"] == 1, records
assert records["detector_released"] == 1, records
assert records["source_released"] == 1, records
assert records["ding"] == [(1, "camera_test")], records
assert len(records["logs"]) == 1, records
assert records["logs"][0]["person_cnt"] == 1, records
assert records["logs"][0]["conf"] == 0.90, records

print("✅ main.py 无硬件集成测试通过")
print(json.dumps(records, ensure_ascii=False, default=str))
