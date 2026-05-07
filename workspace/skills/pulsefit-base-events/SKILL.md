# PulseFit Base 事件解析 Skill

## 功能

将飞书 Base webhook payload 解析为统一格式的字典，供场景路由和 Act skill 使用。

## 解析格式

```python
def parse_base_webhook(payload: dict) -> dict:
    """
    输入：飞书 Base 字段变化 webhook 的原始 JSON payload
    输出：统一格式的事件对象

    统一格式：
    {
        "source": "base",
        "app_token": "<app_token>",
        "table_id": "<table_id>",
        "record_id": "<record_id>",
        "changed_fields": {
            "<field_name>": <new_value>
        },
        "timestamp": "<ISO8601 时间戳>"
    }
    """
```

## 飞书 Base Webhook Payload 结构（参考）

```json
{
  "schema": "base.record_changed.v1",
  "header": {
    "app_id": "cli_xxx",
    "tenant_key": "xxx"
  },
  "event": {
    "app_token": "SvdqbQms3amuT5sgCQicLDzEnDf",
    "table_id": "tblNOgYNV5KYszUl",
    "record_id": "recxxxxxx",
    "fields": {
      "Deliverable Status": "Fully Delivered",
      "Invoice Amount (USD)": 1300
    },
    "change_type": "update_record",
    "update_time": "2026-05-05T12:00:00Z"
  }
}
```

> ⚠️ 注：实际飞书 webhook payload 结构可能略有不同，请以飞书官方文档为准。
> 本 skill 提供解析逻辑，需根据实际 payload 字段名做调整。

## 使用方式

```
收到飞书 webhook → 解析 payload → 调用 scene_routing skill 判断 Act → 执行对应 Act skill
```

## 与 scene_routing 的配合

```python
# 典型调用链
raw_payload = <飞书 webhook POST body>
event = parse_base_webhook(raw_payload)
record_id = event["record_id"]
changed_fields = event["changed_fields"]

# 读取完整记录（用于需要额外字段的场景路由）
full_record = feishu_bitable_app_table_record(
    action="list",
    app_token=event["app_token"],
    table_id=event["table_id"],
    filter={...}
)

scene = route_scene(changed_fields, full_record)
```
