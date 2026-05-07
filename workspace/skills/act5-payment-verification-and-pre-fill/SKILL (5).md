# PulseFit SOP 读取与反哺 Skill

## 功能

读取 SOP 文档内容，并在 Act 5 检测到 SOP 盲区时主动追加评论（反哺循环）。

## 文件路径

- SOP 主文档：`memory/PulseFit_Influencer_Partnership_SOP.md`
- 群聊历史：`memory/PulseFit_Mentor_Chat_History.md`
- Demo Script：`memory/PulseFit_Demo_Script.md`

> 以上文件已存在于 agent workspace memory/ 目录中。

## 读取 SOP 内容

使用 `doc_parse` 工具读取飞书云文档，或直接读取本地 markdown 文件。

```python
# 直接读取（已存储在 workspace）
with open("memory/PulseFit_Influencer_Partnership_SOP.md") as f:
    sop_content = f.read()
```

## 反哺触发条件

当 Agent 在群聊或执行过程中发现：
1. **Paid Usage 设置流程**：Daniel 2026-03-03 给出了 4 步完整流程，但 SOP Appendix B Q1 描述不完整
2. **6 个月 Paid Usage 规则**：Daniel 2026-03-22 补充了数据支撑要求，但 SOP 未收录
3. **W-9 / 合同地址规则**：Daniel 2026-04-05 明确了 W-9 优先原则，但 SOP Section 6.3 只有简单描述

## 反哺文案模板

```markdown
## [自动补充] FAQ 更新候选

**Q: Paid Usage / W-9 规则 / 6个月续期 疑问**
来源：群聊讨论（Daniel，YYYY-MM-DD）
建议补充内容：
<从群聊原文提取的关键规则>

已通知：@Hannah Brooks 确认后更新
```

## 执行方式

1. 用 `feishu_fetch_doc` 读取 SOP 文档
2. 用 `feishu_update_doc` 在 FAQ 区域追加内容
3. 或在 SOP 文档评论区用 `feishu_im_user_message` 提 comment

## 反哺优先级

| 优先级 | 内容 | 来源 |
|--------|------|------|
| P1 | Paid Usage 4 步设置流程（被问了 5 次） | Daniel 2026-03-03 |
| P1 | 6 个月 Paid Usage 需 3 vs 6 数据对比 | Daniel 2026-03-22 |
| P2 | W-9 优先原则 + 合同 amendment | Daniel 2026-04-05 |
| P2 | 6 个月合同加审计条款 | Daniel 2026-03-22 |
