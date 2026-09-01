# -*- coding: utf-8 -*-
"""钉钉通知服务。"""
import json

import requests


class DingTalkService:
    """封装钉钉机器人文本消息发送。"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_alert(self, count_num: int, cam_id: str = "camera_0") -> None:
        """发送人员入侵告警，异常时记录信息但不终止主程序。"""
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"告警[{cam_id}]: Person intrusion detected! No.{count_num}"
            },
        }
        try:
            resp = requests.post(
                self.webhook_url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=5,
            )
            print("【钉钉回执】", resp.text)
        except Exception as err:
            print("钉钉发送异常：", err)