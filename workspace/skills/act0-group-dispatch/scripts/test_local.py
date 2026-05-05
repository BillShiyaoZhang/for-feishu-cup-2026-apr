#!/usr/bin/env python3
"""
本地测试：不需要真实飞书事件，直接传模拟消息。

用法：
  python scripts/test_local.py
"""
import json, subprocess, sys

TEST_EVENTS = [
    # 场景 1：Sophie 问 paid usage（主演示场景）
    {
        "message": {"content": "paid usage 怎么设置？看了文档好像和实际不太一样"},
        "sender": {"name": "Sophie Park"}
    },
    # 场景 2：普通闲聊（不应触发）
    {
        "message": {"content": "大家好！"},
        "sender": {"name": "Hannah Brooks"}
    },
    # 场景 3：问发货流程
    {
        "message": {"content": "合同签了之后可以直接让 Gabriel 发货吗？"},
        "sender": {"name": "Sophie Park"}
    },
]

def run_test(event: dict):
    print(f"\n{'='*50}")
    print(f"输入消息: {event['message']['content']}")
    print(f"发送人: {event['sender']['name']}")
    print(f"{'='*50}")

    result = subprocess.run(
        [sys.executable, "scripts/act0_handler.py"],
        input=json.dumps(event),
        capture_output=True, text=True
    )
    if result.stdout:
        print("输出:", result.stdout)
    if result.stderr:
        print("错误:", result.stderr)


if __name__ == "__main__":
    for event in TEST_EVENTS:
        run_test(event)
