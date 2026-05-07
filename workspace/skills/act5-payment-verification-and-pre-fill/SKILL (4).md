# PulseFit 场景路由 Skill

## 功能

根据飞书 Base 事件 payload，判断应该进入哪个 Act。

## 支持的 Act

- **Act 4**：发货审批（四件自查 + 预填）
- **Act 5**：付款审批（五项校验 + 预填）

## 触发条件速查

| Act | 触发字段 | 触发值 |
|-----|---------|--------|
| Act 4 | `Contract Application` | `Approved` |
| Act 5 | `Payment Trigger` 文本字段 | `Invoice Received` ★ Plan B |
| Act 5 | `Deliverable Status` | `Invoice Received`（需 Base UI 加选项）|
| Act 5 | `Invoice Amount (USD)` | 被填写 + Status 进入 Act 5 阶段（fallback）|

## 路由判断逻辑

```python
APP_TOKEN = "SvdqbQms3amuT5sgCQicLDzEnDf"
TABLE_ID  = "tblNOgYNV5KYszUl"

# Act 4
ACT4_FIELD   = "Contract Application"
ACT4_TRIGGER = "Approved"

# Act 5（Plan B：优先用文本字段）
PAYMENT_TRIGGER_FIELD = "Payment Trigger"
PAYMENT_TRIGGER_VALUE = "Invoice Received"

# Act 5（备选：单选字段，需 UI 加选项）
ACT5_DELIVERABLE_FIELD = "Deliverable Status"
ACT5_DELIVERABLE_VALUE = "Invoice Received"

def route_scene(changed_fields: dict, current_record: dict = None) -> str | None:
    """
    输入：飞书 Base webhook payload 中的 changed_fields（字段名: 新值）
    返回："act4" | "act5" | None
    """

    # ── Act 4：合同审批通过 → 发货 ─────────────────
    if ACT4_FIELD in changed_fields:
        if changed_fields[ACT4_FIELD] == ACT4_TRIGGER:
            return "act4"

    # ── Act 5：Plan B 主路径 ──────────────────────
    # Payment Trigger 文本字段 = "Invoice Received"
    if PAYMENT_TRIGGER_FIELD in changed_fields:
        if changed_fields[PAYMENT_TRIGGER_FIELD] == PAYMENT_TRIGGER_VALUE:
            return "act5"

    # ── Act 5：单选字段备选（需 Base UI 加选项）────
    if ACT5_DELIVERABLE_FIELD in changed_fields:
        if changed_fields[ACT5_DELIVERABLE_FIELD] == ACT5_DELIVERABLE_VALUE:
            return "act5"

    # ── Act 5：fallback ────────────────────────────
    # Invoice Amount 被填写 + Status 已进入 Act 5 阶段
    if "Invoice Amount (USD)" in changed_fields:
        amount = changed_fields["Invoice Amount (USD)"]
        if amount not in (None, ""):
            status = (current_record or {}).get("Status", "")
            if status == "7. Live & Performance / Posted, tracking":
                return "act5"

    return None
```

## 返回值格式

```json
{
  "scene": "act5",
  "record_id": "<触发该事件的 record_id>",
  "trigger_field": "Payment Trigger",
  "trigger_value": "Invoice Received",
  "next_action": "execute_act5_payment_verification"
}
```

## 完整调用链

```
飞书 Base Webhook
    │
    ▼
event_parsing skill（解析 payload）
    │
    ▼
scene_routing skill（判断进入哪个 Act）
    │
    ├── "act4" → act4_shipment_verification skill
    │
    └── "act5" → act5_payment_verification skill
```

## 字段映射依赖

完整字段 ID 映射：`skills/pulsefit-base-reference/field_mapping.yaml`
