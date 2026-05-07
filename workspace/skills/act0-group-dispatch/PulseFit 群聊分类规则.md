# PulseFit 群聊分类规则 Skill

## 功能

对群消息进行 LLM 分类，判断是否是流程类问题、SOP 是否有答案、是否需要触发文档反哺。

## 分类输出字段

```json
{
  "is_question": true,
  "topic": "paid_usage | shipment | contract | payment | sourcing | other",
  "sop_has_answer": false,
  "sop_answer": "SOP 里的原文答案，没有则空字符串",
  "chat_history_has_better_answer": true,
  "chat_history_answer": "Daniel 在群聊里给的更详细答案，没有则空字符串",
  "times_asked": 5,
  "sop_gap": "SOP 缺少的内容描述，用于写文档评论"
}
```

## 触发逻辑

### Part A · 信息分发（每次都触发）

`is_question == true` 时，在群里回复答案卡片。

答案优先级：
1. `chat_history_answer`（Daniel 历史回复，最详细）
2. `sop_answer`（SOP 原文）
3. 兜底文案："请参考 SOP 文档或联系 Daniel。"

来源标注：
- `chat_history_has_better_answer == true` → 来源显示"Daniel 历史群聊回复"
- 否则 → 来源显示"SOP 文档"

### Part B · 文档反哺（满足三条才触发）

| 条件 | 说明 |
|------|------|
| `times_asked >= 2` | 同类问题被问过 2 次以上 |
| `sop_has_answer == false` | SOP 没有给出答案 |
| `chat_history_answer` 非空 | 群聊历史有现成答案可反哺 |

三条同时满足 → 在 SOP 文档写评论 + 私聊 Daniel 确认卡片。

## 模型调用

```python
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
```

输入截断：SOP 内容最多 3000 字符，群聊历史最多 4000 字符，避免超出 context。

## 本地测试（跳过 LLM）

```bash
MOCK_LLM=1 python scripts/act0_handler.py <<< \
  '{"message":{"content":"paid usage 怎么设置"},"sender":{"name":"Sophie Park"}}'
```

Mock 返回固定结果：`topic=paid_usage`，`times_asked=5`，`sop_has_answer=false`。
