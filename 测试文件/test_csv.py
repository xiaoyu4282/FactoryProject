import csv
import os
from datetime import datetime

os.makedirs("./alert_log", exist_ok=True)
csv_path = "./alert_log/alert.csv"

if not os.path.exists(csv_path):
    with open(csv_path,"w",encoding="utf-8",newline="") as f:
        w = csv.writer(f)
        w.writerow(["alert_time","alert_reason","image_path","alert_count"])

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(csv_path,"a",encoding="utf-8",newline="") as f:
    w = csv.writer(f)
    w.writerow([now,"预测试日志","/alert_images/test.jpg",1])

print("✅csv日志写入完成")
