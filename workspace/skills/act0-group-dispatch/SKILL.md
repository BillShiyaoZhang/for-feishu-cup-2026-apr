---
name: act0-group-dispatch
description: >
  监听群聊消息，检测重复问题并立即回答（信息分发）；同时对比 SOP 文档，
  发现知识盲区后在文档写评论建议 Daniel 补充（文档反哺）。
  触发关键词：paid usage, 怎么设置, 流程, SOP, how to, 审批, 发货, 合同
---

# Act 0 · 群聊信息分发 + 文档反哺建议

## 触发条件
- 飞书群消息事件（`im.message.receive_v1`）
- 消息中包含操作流程相关问题

## 动作链
1. LLM 判断消息是否为流程问题
2. **Part A（信息分发）**：从 Mentor Chat History + SOP 提取答案，群里回复交互式卡片
3. **Part B（文档反哺）**：检测 SOP 盲区，在文档写评论 + 私聊 Daniel 确认

## 环境变量
```
SOP_DOC_TOKEN         飞书 SOP 文档的 document token
CHAT_HISTORY_TOKEN    Mentor Chat History 文档的 document token
DANIEL_OPEN_ID        Daniel 的飞书 Open ID
GROUP_CHAT_ID         群聊的 chat_id
```

## 使用方式
```bash
# 手动测试（传入模拟事件）
echo '{"message":{"content":"paid usage 怎么设置"},"sender":{"name":"Sophie Park"}}' \
  | python scripts/act0_handler.py
```
