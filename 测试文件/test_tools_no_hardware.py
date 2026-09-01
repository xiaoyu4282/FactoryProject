# -*- coding: utf-8 -*-
"""无网络、无 OpenCV、无声卡测试 Tools 三个服务的真实实现。"""
import csv
import importlib
import json
import os
import sys
import tempfile
import types

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# 在导入服务前提供最小外部依赖，测试不会连接网络或调用真实 OpenCV。
post_calls = []
requests = types.ModuleType("requests")


def fake_post(url, data=None, headers=None, timeout=None):
    post_calls.append({
        "url": url,
        "data": data,
        "headers": headers,
        "timeout": timeout,
    })
    return types.SimpleNamespace(text='{"errcode":0}')


requests.post = fake_post
sys.modules["requests"] = requests

cv2 = types.ModuleType("cv2")


def fake_imwrite(path, frame):
    with open(path, "wb") as file:
        file.write(b"fake image")
    return True


cv2.imwrite = fake_imwrite
sys.modules["cv2"] = cv2

speech = {"said": [], "stopped": False}


class FakeTts:
    def say(self, text):
        speech["said"].append(text)

    def runAndWait(self):
        pass

    def stop(self):
        speech["stopped"] = True


pyttsx3 = types.ModuleType("pyttsx3")
pyttsx3.init = lambda: FakeTts()
sys.modules["pyttsx3"] = pyttsx3

DingTalkModule = importlib.import_module("Tools.DingTalkService")
LogModule = importlib.import_module("Tools.LogServer")
NotifyModule = importlib.import_module("Tools.NotifyService")

# 1. 钉钉：校验消息格式和超时，不真实发送。
ding = DingTalkModule.DingTalkService("https://example.invalid/webhook")
ding.send_alert(3, "camera_test")
assert len(post_calls) == 1
assert post_calls[0]["timeout"] == 5
payload = json.loads(post_calls[0]["data"].decode("utf-8"))
assert payload["msgtype"] == "text"
assert "camera_test" in payload["text"]["content"]
assert "No.3" in payload["text"]["content"]

# 2. 日志：在临时目录校验截图和 CSV，不污染项目 Logs。
with tempfile.TemporaryDirectory() as temp_dir:
    LogModule.LOG_FOLDER = os.path.join(temp_dir, "Logs")
    LogModule.SNAP_FOLDER = os.path.join(LogModule.LOG_FOLDER, "Images")
    LogModule.CSV_PATH = os.path.join(LogModule.LOG_FOLDER, "LogInfoRecord.csv")
    LogModule.init_log_env()
    LogModule.save_alert_log(1, "person_intrusion", "检测到人员闯入", 1, 0.9,
                             "camera_test", object())

    with open(LogModule.CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    assert rows[0] == [
        "alert_seq", "alert_time", "alert_type", "desc",
        "person_cnt", "conf", "cam_id", "image_path",
    ]
    assert rows[1][0] == "1"
    assert rows[1][2] == "person_intrusion"
    assert rows[1][6] == "camera_test"
    assert os.path.exists(os.path.join(LogModule.LOG_FOLDER, rows[1][7]))

# 3. 语音：校验播报内容和资源停止，不调用真实声卡。
NotifyModule.speak_alert()
assert speech["said"] == ["警告，检测到人员闯入"]
assert speech["stopped"] is True

print("✅ Tools 无硬件测试通过：钉钉、日志截图、CSV、语音均正常")
