# Act 5: Payment Verification & Pre-fill Skill

## 触发条件

**★ Plan B（主要触发）**：`Payment Trigger` 文本字段 = `"Invoice Received"`
**备选**：单选 `Deliverable Status` = `"Invoice Received"`（需 Base UI 加选项）
**Fallback**：`Invoice Amount (USD)` 被填写 + `Status` 进入 `7. Live & Performance / Posted, tracking`

> ✅ `Payment Trigger` 字段已创建（field_id: `fld8qUPbq8`），
> 在 Base 中手动将该字段设为 `"Invoice Received"` 即可触发 Act 5。

---

## 执行步骤

### Step 1: 读取记录（按 record_id）

从 Base `SvdqbQms3amuT5sgCQicLDzEnDf / tblNOgYNV5KYszUl` 读取以下字段：

| 字段 | 用途 |
|------|------|
| ID | 记录标识 |
| Name of Entity | 付款表：Influencer |
| Email | 付款表：Contact |
| Campaign | 付款表：Campaign |
| POC | 通知人 |
| Manage by | 审批人 |
| Contract Amount (USD) | 预填：Contract Amount 核对 |
| Invoice Amount (USD) | 付款表：Invoice Amount |
| GL Number | 付款表：GL Number |
| Payment Due Date | 付款表：Payment Due Date |
| Total Posts Contracted | 校验① |
| Total Posts Delivered | 校验① |
| Bio Link Verified | 校验② |
| Hashtags Verified | 校验③ |
| Paid Usage | 校验④ |
| Performance Updated | 校验⑤ |
| Contract File Link | 付款表：附件 |

---

### Step 2: 五项 Deliverable Verification 校验

**规则来源**：SOP Section 6.1 + Daniel 2026-04-09 群聊

```python
def verify_act5(record) -> dict:
    contracted = record.get("Total Posts Contracted") or 0
    delivered  = record.get("Total Posts Delivered")  or 0

    results = {
        "posts_match":         contracted == delivered,
        "bio_link_verified":   record.get("Bio Link Verified")    == True,
        "hashtags_verified":   record.get("Hashtags Verified")    == True,
        "paid_usage_set":      record.get("Paid Usage")           == True,
        "performance_updated": record.get("Performance Updated")  == True,
    }

    results["can_submit_payment"] = all(results.values())

    results["failed_items"] = [
        label for label, passed in [
            ("Total Posts: Contracted ≠ Delivered", results["posts_match"]),
            ("Bio Link Verified = N",               results["bio_link_verified"]),
            ("Hashtags Verified = N",             results["hashtags_verified"]),
            ("Paid Usage 未设置",                   results["paid_usage_set"]),
            ("Performance 未回写数据库",            results["performance_updated"]),
        ] if not passed
    ]

    return results
```

**Daniel 硬规则（2026-04-09）**：有任何一项为 N，**一律不能提交**付款申请。

---

### Step 3: 生成 Payment Form 预填数据

当 `can_submit_payment == True`：

```json
{
  "scene": "Act5_Payment_Prefill",
  "record_id": "<record_id>",
  "influencer": "<Name of Entity>",
  "payment_form": {
    "influencer":          "<Name of Entity>",
    "contract_amount":    "<Contract Amount (USD)>",
    "invoice_amount":     "<Invoice Amount (USD)>",
    "gl_number":          "<GL Number>",
    "payment_due_date":   "<Payment Due Date>",
    "contract_file_link": "<Contract File Link>",
    "campaign":           "<Campaign>",
    "poc":                "<POC 名称>",
    "managed_by":         "<Manage by 名称>"
  },
  "deliverable_verification": {
    "posts_match":        true,
    "bio_link_verified":  true,
    "hashtags_verified":  true,
    "paid_usage_set":     true,
    "performance_updated": true
  },
  "action": "ready_to_submit"
}
```

当 `can_submit_payment == False`：

```json
{
  "scene": "Act5_Payment_Prefill",
  "record_id": "<record_id>",
  "influencer": "<Name of Entity>",
  "can_submit_payment": false,
  "failed_items": ["<失败项列表>"],
  "action": "do_not_submit",
  "recommendation": "联系博主补全上述项目后重新触发"
}
```

---

### Step 4: 输出结果

**发给 SOPHIE（执行人）**：

```
✅ 付款前 Deliverable Verification 全部通过
💰 Invoice Amount: $<Invoice Amount>
📅 Payment Due: <Payment Due Date>
📋 Payment Form 已预填好，请确认后提交 Payment Application 审批。
```

**如有任何项未通过**：

```
⚠️ Deliverable Verification 未全部通过，不能提交付款申请。
失败的检查项：
1. [具体失败项]
请补全后重新触发。
```

---

## 后续动作（可选）

1. **提交 Payment Application 审批** → `Payment Application = Pending`
2. **审批通过后回写**：
   - `Payment Form Status = Approved`
   - `Payment Application = Approved`

---

## 字段依赖

- app_token: `SvdqbQms3amuT5sgCQicLDzEnDf`
- table_id: `tblNOgYNV5KYszUl`
- `Payment Trigger` 字段: `fld8qUPbq8`（触发信号）
- 完整字段映射：`skills/pulsefit-base-reference/field_mapping.yaml`

## 规则来源索引

- 五项校验：SOP Section 6.1
- 任何 N 都不能提交：Daniel 2026-04-09 群聊
- Paid Usage 默认 3 个月 / 6 个月需数据支撑：Daniel 2026-02-20 / 2026-03-22 群聊；SOP Section 5.2

## 测试脚本

`simulate_act5.py` — 可独立运行的两场景测试（CT002 全绿 / CT004 失败）
