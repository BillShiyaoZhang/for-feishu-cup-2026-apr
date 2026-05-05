#!/usr/bin/env python3
"""
Demo 触发脚本：Sophie 重演关键聊天记录，最后提问触发 KnowAgent。

用法：
  export $(grep -v '^#' .env | xargs)
  python scripts/demo_trigger.py
"""
import subprocess, json, os, time, sys

GROUP_CHAT_ID   = os.environ["GROUP_CHAT_ID"]
SOPHIE_PROFILE  = os.environ.get("SOPHIE_PROFILE", "feishu-amy-bot")
DANIEL_PROFILE  = os.environ.get("DANIEL_PROFILE", "feishu-daniel")

# ── 发消息工具 ────────────────────────────────────────────────

def send(profile: str, chat_id: str, text: str, delay: float = 1.5):
    result = subprocess.run([
        "lark-cli", "--profile", profile,
        "im", "+messages-send", "--as", "bot",
        "--chat-id", chat_id,
        "--msg-type", "text",
        "--content", json.dumps({"text": text})
    ], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        status = "✅" if data.get("ok") else "❌"
        print(f"{status} [{profile}] {text[:50]}")
        if not data.get("ok"):
            print(f"   error: {data}")
    except Exception:
        print(f"❌ parse error: {result.stderr[:100]}")
    time.sleep(delay)


def sophie(text: str, delay: float = 1.5):
    send(SOPHIE_PROFILE, GROUP_CHAT_ID, text, delay)

def daniel(text: str, delay: float = 1.5):
    send(DANIEL_PROFILE, GROUP_CHAT_ID, text, delay)


# ── Demo 剧本 ────────────────────────────────────────────────

SCRIPT = [
    # 幕一：日常运营背景
    ("sophie", "早安大家 👋 今天有 3 个新博主要跟进，我先更新一下 database"),
    ("sophie", "jadeclifftrains（IG 45k，跑步居家训练）—— 建议 PulseRope Pro，报价我算了一下 $1200"),
    ("sophie", "Daniel @ 你 这个博主 maxstone_fit 报价我算出来 $5200，IG 138k 粉，您看可以发吗？"),
    ("daniel", "可以发。但第一次报价压到 $4500，留点谈判空间"),
    ("sophie", "好的，我先在 database 更新 status，再发邮件 ✅"),

    # 幕二：合同流程
    ("sophie", "Daniel morganbrooks_fit 合同博主已经签字回传了，我直接让 Gabriel 发货可以吗？"),
    ("daniel", "必须先走审批，发货是合同审批通过之后的事。你今天先把 contract application 提交上来"),
    ("sophie", "好的明白了，我现在去填 Contract Application"),

    # 幕三：第一次问 paid usage
    ("sophie", "请问 paid usage 怎么设置呀？看了文档好像和实际不太一样 🤔"),
    ("daniel", "旧的 paid usage setup guide 已经弃用了，简单说：\n1. Meta Business Suite → Branded Content → Approve creator\n2. 博主 IG settings 加我们为 paid partner\n3. 博主发布时勾选 Paid Partnership\n4. 我们后台开启 boosting 权限\n\n我下次更新一下 SOP"),
    ("sophie", "好的谢谢 Daniel！我按步骤操作一下 🙏"),

    # 幕四：付款流程
    ("sophie", "Daniel harperwellness 的内容全部上线了，invoice 和 W-9 也收齐了，可以提交付款申请吗"),
    ("daniel", "先核对 Deliverable Verification，有任何一项 N 都不能提交"),
    ("sophie", "检查完了，bio link 在、hashtags 对、paid usage 设了、performance 数据也回写了 ✅"),

    # 幕五：触发消息 —— KnowAgent 上场
    ("sophie", "paid usage 那个我又有点忘了步骤…… 😅 有人记得吗？"),
]

if __name__ == "__main__":
    print("=" * 55)
    print("  PulseFit KnowAgent · Act 0 Demo")
    print("=" * 55)
    print()

    for i, (role, text) in enumerate(SCRIPT):
        is_last = (i == len(SCRIPT) - 1)
        delay = 3.0 if is_last else 1.5
        if role == "daniel":
            daniel(text, delay)
        else:
            sophie(text, delay)

    print()
    print("📨 触发消息已发送 — 等待 KnowAgent 回复...")
    print()
    print("现在运行：")
    print("  MOCK_LLM=1 python scripts/act0_handler.py <<< '{\"message\":{\"content\":\"paid usage 那个我又有点忘了步骤\"},\"sender\":{\"name\":\"Sophie Park\"}}'")
