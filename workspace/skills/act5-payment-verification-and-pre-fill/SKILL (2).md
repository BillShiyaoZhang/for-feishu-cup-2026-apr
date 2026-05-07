# PulseFit Base 读写 Skill

## 功能

读写飞书多维表格记录，是所有 Act 的数据基础。

## 配置

- **app_token**: `SvdqbQms3amuT5sgCQicLDzEnDf`
- **table_id**: `tblNOgYNV5KYszUl`
- **Base URL**: `https://jcneyh7qlo8i.feishu.cn/base/SvdqbQms3amuT5sgCQicLDzEnDf`

## 工具调用

使用 `feishu_bitable_app_table_record` 工具，action 支持：
- `list`：查询/搜索记录
- `create`：创建记录
- `update`：更新单条记录
- `batch_update`：批量更新

使用 `feishu_bitable_app_table_field` 工具，action 支持：
- `list`：列出所有字段（字段名 → field_id 映射）

## 常用操作

### 读取单条记录

```
feishu_bitable_app_table_record(
    action="list",
    app_token="SvdqbQms3amuT5sgCQicLDzEnDf",
    table_id="tblNOgYNV5KYszUl",
    filter={
        "conjunction": "and",
        "conditions": [
            {"field_name": "ID", "operator": "is", "value": ["<record_id>"]}
        ]
    }
)
```

### 按 ID 精确查找记录（推荐方式）

```
feishu_bitable_app_table_record(
    action="list",
    app_token="SvdqbQms3amuT5sgCQicLDzEnDf",
    table_id="tblNOgYNV5KYszUl",
    filter={
        "conjunction": "and",
        "conditions": [
            {"field_name": "ID", "operator": "is", "value": ["<ID值>"]}
        ]
    }
)
```

### 搜索特定 Status 的记录

```
filter={
    "conjunction": "and",
    "conditions": [
        {"field_name": "Status", "operator": "is", "value": ["7. Live & Performance / Posted, tracking"]}
    ]
}
```

### 更新记录字段

```
feishu_bitable_app_table_record(
    action="update",
    app_token="SvdqbQms3amuT5sgCQicLDzEnDf",
    table_id="tblNOgYNV5KYszUl",
    record_id="<record_id>",
    fields={
        "Payment Application": "Pending",
        "Payment Form Status": "Pending"
    }
)
```

## Act 4 回写（审批通过后）

```python
act4_post_approval_updates = {
    "Shipment Form Status": "Approved",
    "Payment Application": "Not Submitted",
    # Order Number (SH) 在 Gabriel 发货后回写
}
```

## Act 5 回写（审批通过后）

```python
act5_post_approval_updates = {
    "Payment Form Status": "Approved",
    "Payment Application": "Approved"
}
```

## 字段映射

完整字段 ID → 字段名对照表：
`skills/pulsefit-base-reference/field_mapping.yaml`
