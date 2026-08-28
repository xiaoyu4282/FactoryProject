import requests
import json

# ==========这里粘贴你的完整webhook链接==========
webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=5806c8e908d20c707ca3d8a729bf54af17cb098673828b43ef0d49c53ce159c0"
# ==============================================

payload = {
    "msgtype": "text",
    "text": {
        "content": "告警：钉钉机器人连通性测试！"
    }
}

try:
    resp = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={"Content-Type":"application/json"},
        timeout=8
    )
    print("状态码:", resp.status_code)
    print("钉钉返回结果:", resp.text)

except Exception as err:
    print("请求异常：", err)