---
name: pulsefit-knowledge-graph
description: >
  PulseFit网红营销Knowledge Agent知识图谱管理工具。用于查询、新增、更新、删除KG中的实体和事件数据。
  触发关键词：知识图谱, KG, 查询实体, 新增实体, 查询事件, 记录事件, 记忆
---

# PulseFit 知识图谱管理 Skill
本Skill管理PulseFit场景的知识图谱实例数据。本体（ontology skill）定义Schema，本Skill维护实际业务数据。

## 文件结构
```
skills/knowledge-graph/
├── SKILL.md                     ← 本文件
├── README.md                    ← 使用指南
├── kg/
│   ├── graph.trig               ← 核心KG：静态实体（网红、产品、员工、规则等）
│   └── graph-events-YYYY-QN.trig ← 事件KG：按季度分区存储业务事件
└── scripts/
    ├── query_entity.py          ← 关键词查询实体
    ├── query_events.py          ← 查询事件（按时间、人员、类型）
    ├── query_natural.py         ← 自然语言查询
    ├── manage_entity.py         ← 实体增删改查
    └── migrate_events.py        ← 事件迁移工具
```

## 核心功能
### 1. 查询实体
根据关键词查询KG中的实体：
```bash
python skills/knowledge-graph/scripts/query_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --query "jadeclifftrains 博主信息"
```

### 2. 查询事件
按条件查询事件：
```bash
# 按时间范围查询
python skills/knowledge-graph/scripts/query_events.py \
  --from 2026-04-01 --to 2026-04-30

# 按人员查询
python skills/knowledge-graph/scripts/query_events.py \
  --person kg:person-sophie --from 2026-04-01

# 按事件类型查询
python skills/knowledge-graph/scripts/query_events.py \
  --event-type approval_pass --from 2026-04-01
```

### 3. 自然语言查询
直接用自然语言查询KG：
```bash
python skills/knowledge-graph/scripts/query_natural.py \
  "jadeclifftrains的合同金额是多少？"
```
返回结构化查询结果，包含schema上下文避免幻觉。

### 4. 管理实体
新增/更新/删除实体：
```bash
# 新增网红
python skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type influencer --id jadeclifftrains \
  --name "jadeclifftrains" \
  --prop "pulsefit:followerCount=45000" \
  --prop "pulsefit:platform=Instagram" \
  --prop "pulsefit:contentType=跑步,居家训练"

# 新增发货单
python skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type shipment_order --id shipment-20260428-001 \
  --name "jadeclifftrains发货单" \
  --prop "pulsefit:shipmentStatus=pending" \
  --prop "pulsefit:hasContract=kg:contract-jadeclifftrains-2026"

# 删除实体
python skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type influencer --id jadeclifftrains --delete
```

### 5. 记录事件
新增业务事件：
```bash
python skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph-events-2026-Q2.trig \
  --type event \
  --id event-approval-pass-20260428-001 \
  --name "jadeclifftrains发货审批通过" \
  --description "Daniel批准了jadeclifftrains的发货申请" \
  --event-type approval_pass \
  --event-time "2026-04-28T10:00:00+08:00" \
  --agent kg:person-daniel
```

## 实体类型列表
| 类型 | 对应本体类 | 存储文件 |
|---|---|---|
| `person` | `pulsefit:Person` | `graph.trig` |
| `employee` | `pulsefit:Employee` | `graph.trig` |
| `influencer` | `pulsefit:Influencer` | `graph.trig` |
| `product` | `pulsefit:Product` | `graph.trig` |
| `campaign` | `pulsefit:Campaign` | `graph.trig` |
| `contract` | `pulsefit:Contract` | `graph.trig` |
| `content` | `pulsefit:ContentDeliverable` | `graph.trig` |
| `approval` | `pulsefit:ApprovalFlow` | `graph.trig` |
| `shipment` | `pulsefit:ShipmentOrder` | `graph.trig` |
| `payment` | `pulsefit:PaymentOrder` | `graph.trig` |
| `rule` | `pulsefit:BusinessRule` | `graph.trig` |
| `event` | `pulsefit:BusinessEvent` | `graph-events-YYYY-QN.trig` |

## 约束规则
1. 所有新增实体必须使用本体中已定义的类和属性
2. 事件按季度存储到对应的graph-events文件中
3. 实体ID使用kebab-case，格式：`[类型缩写]-[名称/日期]-[序号]`
4. 实体ID中禁止使用`/`，使用`-`代替
5. 所有操作自动备份，操作前自动运行SHACL校验
