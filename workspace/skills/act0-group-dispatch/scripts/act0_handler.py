#!/usr/bin/env python3
"""
Act 0: 群聊信息分发 + 文档反哺建议
触发: im.message.receive_v1 事件，消息含流程类问题关键词
"""
import subprocess, json, sys, os
import anthropic

client = anthropic.Anthropic()

SOP_DOC_TOKEN      = os.environ["SOP_DOC_TOKEN"]
CHAT_HISTORY_TOKEN = os.environ["CHAT_HISTORY_TOKEN"]
DANIEL_OPEN_ID     = os.environ["DANIEL_OPEN_ID"]
GROUP_CHAT_ID      = os.environ["GROUP_CHAT_ID"]


# ── 飞书工具函数 ──────────────────────────────────────────────

LARK_PROFILE = os.environ.get("LARK_PROFILE", "")

def lark(cmd: list[str]) -> dict:
    base = ["lark-cli"]
    if LARK_PROFILE:
        base += ["--profile", LARK_PROFILE]
    result = subprocess.run(base + cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stderr}


def read_doc(token: str) -> str:
    r = lark(["docs", "+fetch", "--api-version", "v2",
               "--doc", token, "--scope", "content", "--doc-format", "markdown"])
    return r.get("data", {}).get("content", "")


def send_card(chat_id: str, card: dict):
    lark(["im", "+messages-send", "--as", "bot",
          "--chat-id", chat_id,
          "--msg-type", "interactive",
          "--content", json.dumps(card)])


def send_p2p_card(open_id: str, card: dict):
    lark(["im", "+messages-send", "--as", "bot",
          "--user-id", open_id,
          "--msg-type", "interactive",
          "--content", json.dumps(card)])


def add_doc_comment(token: str, content: str):
    lark(["docs", "comment", "create", "--api-version", "v2",
          "--doc", token,
          "--content", json.dumps({"content": content})])


def append_to_doc(token: str, content: str):
    lark(["docs", "+update", "--api-version", "v2",
          "--doc", token,
          "--command", "append",
          "--doc-format", "markdown",
          "--content", content])


# ── LLM 分析 ─────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
你是 PulseFit 团队的 KnowAgent。

群里收到消息："{msg}"

以下是团队 SOP 文档（节选）：
{sop}

以下是历史群聊记录：
{history}

请判断并返回 JSON（只返回 JSON，不要加任何说明）：
{{
  "is_question": true/false,
  "topic": "paid_usage" | "shipment" | "contract" | "payment" | "sourcing" | "other",
  "sop_has_answer": true/false,
  "sop_answer": "SOP 里的原文答案，没有则空字符串",
  "chat_history_has_better_answer": true/false,
  "chat_history_answer": "Daniel 在群聊里给的更详细答案，没有则空字符串",
  "times_asked": 历史群聊里被问过几次（整数）,
  "sop_gap": "SOP 缺少的内容描述，用于写文档评论"
}}
"""


def classify(msg: str, sop: str, history: str) -> dict:
    if os.environ.get("MOCK_LLM"):
        return {
            "is_question": True,
            "topic": "paid_usage",
            "sop_has_answer": False,
            "sop_answer": "",
            "chat_history_has_better_answer": True,
            "chat_history_answer": (
                "Paid usage 设置步骤：\n"
                "1. 进入 Creator Dashboard → Monetization\n"
                "2. 开启 Paid Content 开关\n"
                "3. 设置单价（建议 $2–5）\n"
                "4. 提交审核，1–2 个工作日生效"
            ),
            "times_asked": 5,
            "sop_gap": "SOP FAQ Q1 缺少 paid usage 具体操作步骤"
        }
    prompt = CLASSIFY_PROMPT.format(
        msg=msg,
        sop=sop[:3000],
        history=history[:4000]
    )
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.content[0].text)


# ── 卡片构建 ─────────────────────────────────────────────────

def build_answer_card(sender_name: str, answer: str, source: str) -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "💡 流程说明"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md",
             "content": f"**@{sender_name}** 我查到了相关流程 👇\n\n{answer}"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [
                {"tag": "plain_text", "content": f"来源：{source} · KnowAgent 自动检索"}
            ]}
        ]
    }


def build_doc_comment(msg: str, count: int, suggested: str) -> str:
    return (
        f"@Daniel · KnowAgent 自动检测\n\n"
        f"📊 检测到该文档存在信息缺口：\n"
        f"过去群聊内 {count} 位同事追问\"{msg[:40]}...\"，\n"
        f"但本文档没有给出具体步骤。\n\n"
        f"💡 建议补充（基于您的历史回复）：\n{suggested}\n\n"
        f"[采纳建议] [查看原始证据] [忽略]"
    )


def build_daniel_card(count: int, suggested: str) -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📝 SOP 更新建议"},
            "template": "orange"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md",
             "content": (
                 f"检测到 SOP 知识盲区，过去 **{count}** 次被追问，"
                 f"建议补充以下内容到 SOP 附录 B：\n\n{suggested}"
             )}},
            {"tag": "action", "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✅ 采纳，写入 SOP"},
                    "type": "primary",
                    "value": {"action": "approve_feedback",
                              "content": suggested,
                              "doc_token": SOP_DOC_TOKEN}
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "忽略"},
                    "type": "default",
                    "value": {"action": "ignore_feedback"}
                }
            ]}
        ]
    }


# ── 卡片回调处理（Daniel 点"采纳"时触发）────────────────────

def handle_card_callback(event: dict):
    value = event.get("action", {}).get("value", {})
    action = value.get("action")

    if action == "approve_feedback":
        content = value.get("content", "")
        doc_token = value.get("doc_token", SOP_DOC_TOKEN)
        # 把 Daniel 的答案追加写入 SOP 附录 B
        append_to_doc(doc_token, f"\n\n### 补充（由 KnowAgent 自动写入）\n\n{content}\n")
        # 回复 Daniel 确认
        send_p2p_card(DANIEL_OPEN_ID, {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "✅ 已写入 SOP"},
                       "template": "green"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md",
                          "content": "内容已追加到 SOP 附录 B，感谢确认！"}}]
        })


# ── 主入口 ───────────────────────────────────────────────────

def handle(event: dict):
    # 区分消息事件 vs 卡片回调
    event_type = event.get("type") or event.get("event_type", "")
    if "card" in event_type or event.get("action"):
        handle_card_callback(event)
        return

    msg_text = event.get("message", {}).get("content", "")
    sender_name = event.get("sender", {}).get("name", "同事")

    # 过滤空消息
    if not msg_text.strip():
        return

    # 读取知识源
    sop_content     = read_doc(SOP_DOC_TOKEN)
    chat_history    = read_doc(CHAT_HISTORY_TOKEN)

    # LLM 分类
    result = classify(msg_text, sop_content, chat_history)

    if not result.get("is_question"):
        return

    # Part A：信息分发 — 群里回复答案
    answer = (result.get("chat_history_answer")
              or result.get("sop_answer")
              or "请参考 SOP 文档或联系 Daniel。")
    source = ("Daniel 历史群聊回复"
              if result.get("chat_history_has_better_answer")
              else "SOP 文档")

    send_card(GROUP_CHAT_ID, build_answer_card(sender_name, answer, source))

    # Part B：文档反哺 — SOP 有盲区且被问过 2+ 次
    count = result.get("times_asked", 0)
    if count >= 2 and not result.get("sop_has_answer") and result.get("chat_history_answer"):
        suggested = result["chat_history_answer"]

        # 在 SOP 文档写评论
        add_doc_comment(SOP_DOC_TOKEN,
                        build_doc_comment(msg_text, count, suggested))

        # 私聊 Daniel 确认卡片
        send_p2p_card(DANIEL_OPEN_ID,
                      build_daniel_card(count, suggested))


if __name__ == "__main__":
    event = json.load(sys.stdin)
    handle(event)
