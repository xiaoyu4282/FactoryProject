import requests
import json

DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"


payload = {
    "msgtype": "text",
    "text": {"content":"【告警】盒子环境测试：无摄像头，仅测试钉钉通路"}
}

resp = requests.post(DINGDING_WEBHOOK, json=payload)
print(f"HTTP响应码：{resp.status_code}")
if resp.status_code == 200:
    print("✅钉钉机器人通信正常，盒子外网访问没问题")
else:
    print("❌钉钉发送失败，检查webhook和盒子网络")
