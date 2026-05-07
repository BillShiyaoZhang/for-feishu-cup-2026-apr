# PulseFit 审批创建与查询 Skill

## 功能

创建飞书审批实例，查询审批状态，处理审批回调。

## 审批配置

当前 Demo 共三次审批：

| 审批 | 触发时机 | 回写字段 |
|------|---------|---------|
| Contract Application | 博主签回合同 | `Contract Application = Approved` |
| Shipment Application | Act 4 四件自查全过 | `Shipment Form Status = Approved` |
| Payment Application | Act 5 五项 Verification 全 Y | `Payment Form Status = Approved` |

## 创建审批

使用飞书审批 API：
- 工具：`feishu_calendar_event`（不支持审批创建）
- ⚠️ 当前 agent 的飞书工具集中**未包含审批创建工具**（`feishu_approval_*` 未在已启用列表中）

**Workaround 方案（无审批 API 时的替代）**：

方案 A：使用飞书消息卡片模拟审批
```
发送交互式卡片 → 用户点击"提交审批" → 卡片回调 → Agent 收到回调 → 更新 Base 状态
```

方案 B：生成预填数据后通知 SOPHIE 手动提交审批
```
Agent 输出付款表预填内容 → 通知 SOPHIE 登录飞书审批后台提交
```

方案 C（推荐）：在 Base 中新建「审批记录表」，Agent 插入一行审批请求，SOPHIE 从表中取数据手动提交审批，审批结果通过 Base 字段同步

## 回写操作（审批通过后）

使用 `feishu_bitable_app_table_record` 的 `update` action：

```python
# Act 4 通过后
{
    "Shipment Form Status": "Approved"
}

# Act 5 通过后
{
    "Payment Form Status": "Approved",
    "Payment Application": "Approved"
}
```

## 审批查询

当飞书审批 webhook 回调到达时（若已接入审批事件）：
```python
# 解析审批回调 payload
{
    "approval_code": "<approval_code>",
    "instance_id": "<instance_id>",
    "status": "approved",  # approved / rejected
    "record_id": "<关联的 record_id>"
}
```

## 建议接入顺序

1. 先用 Base 字段模拟审批状态（SOPHIE 手动更新 `Contract Application = Approved`）
2. Act 4 / Act 5 输出预填数据，SOPHIE 手动提交审批
3. 最后接入飞书审批 API，实现自动化
