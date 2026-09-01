# -*- coding: utf-8 -*-
"""本地通知服务。"""


def speak_alert() -> None:
    """播报人员入侵告警；依赖缺失或播报失败时不终止主程序。"""
    try:
        import pyttsx3

        tts = pyttsx3.init()
        tts.say("警告，检测到人员闯入")
        tts.runAndWait()
        tts.stop()
    except Exception as err:
        print("语音播报异常：", err)
