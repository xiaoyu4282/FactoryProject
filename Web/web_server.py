# -*- coding: utf-8 -*-
"""
Web 服务：实时视频流 + 前端页面（后续在此扩展配置接口）。
在独立后台线程中运行 Flask，通过共享 FrameBuffer 与主循环交换画面。
"""
import threading
import time

import cv2
from flask import Flask, Response, jsonify, render_template


def create_app(frame_buffer, cam_ids):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("dashboard.html", cam_ids=cam_ids)

    @app.route("/api/cameras")
    def cameras():
        return jsonify({"cameras": cam_ids})

    @app.route("/video_feed/<cam_id>")
    def video_feed(cam_id):
        def generate():
            last_seq = -1
            while True:
                frame, seq = frame_buffer.get(cam_id)
                if frame is None or seq == last_seq:
                    # 没有新帧，稍等再取，避免空转重复发送同一帧
                    time.sleep(0.03)
                    continue
                last_seq = seq
                ok, buf = cv2.imencode(".jpg", frame)
                if not ok:
                    continue
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n"
                       + buf.tobytes() + b"\r\n")

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    return app


def start_web_server(frame_buffer, cam_ids, host="0.0.0.0", port=8000):
    """在后台线程启动 Web 服务（不阻塞主循环），返回 Flask app。"""
    app = create_app(frame_buffer, cam_ids)
    thread = threading.Thread(
        target=lambda: app.run(
            host=host, port=port, threaded=True,
            debug=False, use_reloader=False,
        ),
        daemon=True,
        name="web-server",
    )
    thread.start()
    print(f"🌐 Web 服务已启动: http://{host}:{port}")
    return app
