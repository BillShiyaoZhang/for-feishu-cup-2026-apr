#!/usr/bin/env python3
"""
在 OpenClaw 里注册 Act 0 的群消息事件监听。
运行一次即可，不需要重复执行。

用法：
  python scripts/register_event.py
"""
import subprocess, json

def openclaw(cmd: list[str]) -> dict:
    result = subprocess.run(["openclaw"] + cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout)
        return {}


def main():
    # 注册飞书群消息事件 → 路由到 act0 skill
    result = openclaw([
        "event", "subscribe",
        "--event-type", "im.message.receive_v1",
        "--skill", "act0-group-dispatch",
        "--handler", "scripts/act0_handler.py",
        "--filter", '{"chat_type": "group"}'   # 只处理群消息，不处理私聊
    ])
    print("注册结果:", json.dumps(result, ensure_ascii=False, indent=2))

    # 注册卡片回调（Daniel 点按钮时）
    result2 = openclaw([
        "event", "subscribe",
        "--event-type", "card.action.trigger",
        "--skill", "act0-group-dispatch",
        "--handler", "scripts/act0_handler.py"
    ])
    print("卡片回调注册结果:", json.dumps(result2, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
