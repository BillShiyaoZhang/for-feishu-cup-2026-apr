# PulseFit 群消息解析 Skill

## 功能

将飞书群消息事件 payload 解析为统一格式，供 Act 0 分类和处理使用。

## 解析格式

```python
def parse_group_message(event: dict) -> dict:
    """
    输入：im.message.receive_v1 飞书事件原始 JSON
    输出：统一格式的消息对象

    统一格式：
    {
        "msg_text":     str,   # 消息正文
        "sender_name":  str,   # 发送人名称
        "chat_id":      str,   # 群聊 ID
        "event_type":   str,   # 事件类型（message / card_callback）
    }
    """
```

## 事件类型区分

| event_type 特征 | 处理路径 |
|----------------|---------|
| `"card"` in event_type 或有 `"action"` 字段 | → `handle_card_callback()` |
| 其余 | → 正常群消息处理流程 |

## 字段提取

```python
msg_text    = event.get("message", {}).get("content", "")
sender_name = event.get("sender", {}).get("name", "同事")
event_type  = event.get("type") or event.get("event_type", "")
```

## 过滤规则

- 消息正文为空 → 直接返回，不处理
- 非群消息（私聊）→ 由 OpenClaw 事件过滤器拦截（`--filter '{"chat_type": "group"}'`）
