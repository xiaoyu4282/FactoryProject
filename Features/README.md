# Features 业务功能包

每项业务功能使用独立子目录，避免把规则持续堆积到 `main.py`。

- `intrusion`：禁区入侵告警
- `absence`：离岗脱岗告警
- `fire_smoke`：烟火烟雾检测
- `crowd`：人员聚集告警
- `animal`：动物越线闯入告警
- `area_count`：指定区域实时人数统计

`Tools` 只存放钉钉、日志、语音等可被多个业务复用的基础能力。
