# Act 0 · 群聊信息分发 + 文档反哺建议

PulseFit KnowAgent — OpenClaw 赛道 · 飞书校园 AI 大赛

## 功能

1. **信息分发**：Sophie 在群里问操作流程 → Agent 秒答（从 SOP + Mentor Chat History 提取）
2. **文档反哺**：检测到 SOP 有盲区且被问过 2+ 次 → 在文档写评论 + 私聊 Daniel 确认 → Daniel 一键写入 SOP

## 文件结构

```
act0-group-dispatch/
├── SKILL.md                  # OpenClaw skill 描述
├── scripts/
│   ├── act0_handler.py       # 主处理逻辑
│   ├── register_event.py     # 注册飞书事件（运行一次）
│   └── test_local.py         # 本地测试
├── .env.example              # 环境变量模板
└── README.md
```

## 部署步骤

### 1. 准备飞书文档

把以下两个文件上传到飞书云文档：
- `PulseFit_Influencer_Partnership_SOP.md`
- `PulseFit_Mentor_Chat_History.md`

### 2. 获取 Token

**文档 token（SOP_DOC_TOKEN / CHAT_HISTORY_TOKEN）**：

打开飞书文档，URL 格式如下：
```
https://xxx.feishu.cn/docx/doxcnABCDEFGHIJKLMN
                              ^^^^^^^^^^^^^^^^^^^
                              这就是 document_token
```
或用 lark-cli 查询：
```bash
lark-cli docs +search --query "PulseFit SOP" --api-version v2
```

**Daniel 的 Open ID（DANIEL_OPEN_ID）**：
```bash
lark-cli contact user get --name "Daniel Tobias"
# 返回结果里的 open_id 字段，格式：ou_xxxxxxxx
```

**群聊 chat_id（GROUP_CHAT_ID）**：
```bash
lark-cli im chat list
# 找到 "PulseFit · Influencer Contact 组"，取 chat_id
# 格式：oc_xxxxxxxx
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入真实值
```

### 4. 注册事件（在 OpenClaw 环境里执行）

```bash
python scripts/register_event.py
```

### 5. 本地测试

```bash
export $(cat .env | xargs)
python scripts/test_local.py
```

## Demo 触发路径

```
Sophie 在群里发：paid usage 怎么设置？
    ↓ (3秒内)
KnowAgent 在群里回复答案卡片（来源：Daniel 2026-03-03 群聊）
    ↓ (同时)
KnowAgent 在 SOP 文档写评论（检测到 5 次被追问，SOP 无答案）
    ↓
Daniel 私聊收到确认卡片 → 点[采纳]
    ↓
KnowAgent 把 4 步流程写入 SOP 附录 B
```

整个流程 Sophie 操作 1 次，Daniel 操作 1 次。
