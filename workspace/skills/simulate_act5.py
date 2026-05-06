#!/usr/bin/env python3
"""
Act 5 端到端模拟测试
- CT002: 五项全部通过 + Payment Trigger = Invoice Received → 生成付款表预填
- CT004: 三项失败 → 显示失败项，不生成预填
- 路由判断：Payment Trigger = "Invoice Received" → 触发 Act 5
"""

import json
from datetime import datetime

# ── 触发字段常量 ───────────────────────────────────────────
PAYMENT_TRIGGER_FIELD = "Payment Trigger"
PAYMENT_TRIGGER_VALUE = "Invoice Received"   # ★ Plan B 触发值

def ts_to_date(val):
    if not val:
        return "未填"
    if val > 1e12:
        return datetime.fromtimestamp(val / 1000).strftime("%Y-%m-%d")
    return datetime.fromtimestamp(val).strftime("%Y-%m-%d")


# ── Plan B 路由判断 ─────────────────────────────────────────
def route_scene(changed_fields: dict, current_record: dict = None) -> str | None:
    """模拟 scene_routing skill"""
    if PAYMENT_TRIGGER_FIELD in changed_fields:
        if changed_fields[PAYMENT_TRIGGER_FIELD] == PAYMENT_TRIGGER_VALUE:
            return "act5"
    if "Deliverable Status" in changed_fields:
        if changed_fields["Deliverable Status"] == "Invoice Received":
            return "act5"
    if "Contract Application" in changed_fields:
        if changed_fields["Contract Application"] == "Approved":
            return "act4"
    return None


# ── Act 5 校验 ─────────────────────────────────────────────
def verify_act5(record):
    contracted = record.get("Total Posts Contracted") or 0
    delivered  = record.get("Total Posts Delivered")  or 0
    results = {
        "posts_match":         contracted == delivered,
        "bio_link_verified":   record.get("Bio Link Verified")    == True,
        "hashtags_verified":   record.get("Hashtags Verified")    == True,
        "paid_usage_set":      record.get("Paid Usage")           == True,
        "performance_updated": record.get("Performance Updated")  == True,
    }
    results["can_submit_payment"] = all(results.values())
    results["failed_items"] = [
        label for label, passed in [
            ("Total Posts: Contracted ≠ Delivered", results["posts_match"]),
            ("Bio Link Verified = N",               results["bio_link_verified"]),
            ("Hashtags Verified = N",             results["hashtags_verified"]),
            ("Paid Usage 未设置",                   results["paid_usage_set"]),
            ("Performance 未回写数据库",            results["performance_updated"]),
        ] if not passed
    ]
    return results


# ── Act 5 执行 ──────────────────────────────────────────────
def execute_act5(record):
    print(f"\n📖 读取记录: {record['record_id']}")
    print(f"   Name: {record.get('Name of Entity', 'N/A')}")

    v = verify_act5(record)
    print(f"\n🔍 五项 Deliverable Verification 校验")
    for k, passed in [
        ("posts_match",         v["posts_match"]),
        ("bio_link_verified",   v["bio_link_verified"]),
        ("hashtags_verified",   v["hashtags_verified"]),
        ("paid_usage_set",      v["paid_usage_set"]),
        ("performance_updated", v["performance_updated"]),
    ]:
        print(f"   {'✅' if passed else '❌'} {k}: {passed}")

    if v["can_submit_payment"]:
        print(f"\n✅ CAN SUBMIT → 生成 Payment Form 预填数据")
        print(f"   influencer         : {record.get('Name of Entity', '')}")
        print(f"   invoice_amount      : ${record.get('Invoice Amount (USD)', 0)}")
        print(f"   gl_number           : {record.get('GL Number', '')}")
        print(f"   payment_due_date   : {ts_to_date(record.get('Payment Due Date'))}")
        print(f"\n📤 飞书消息:")
        print(f"""✅ 付款前 Deliverable Verification 全部通过
💰 Invoice Amount: ${record.get('Invoice Amount (USD)', 0)}
📅 Payment Due: {ts_to_date(record.get('Payment Due Date'))}
📋 Payment Form 已预填好，请确认后提交 Payment Application 审批。""")
    else:
        print(f"\n❌ CANNOT SUBMIT → 显示失败项")
        for i, item in enumerate(v["failed_items"]):
            print(f"   {i+1}. {item}")
        print(f"\n📤 飞书消息:")
        items = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(v["failed_items"]))
        print(f"""⚠️ Deliverable Verification 未全部通过，不能提交付款申请。
失败的检查项：
{items}
请补全后重新触发。""")

    return v


# ── 测试数据 ─────────────────────────────────────────────────
# CT002: 五项全绿 + Payment Trigger = Invoice Received
CT002 = {
    "record_id": "recvi5N0H8mXPs",
    "Name of Entity": "morganbrooks_fit Inc",
    "Campaign": "PulseRope Holiday Push",
    "Contract Amount (USD)": 3800,
    "Invoice Amount (USD)": 3800,
    "GL Number": "GL-1002",
    "Payment Due Date": 1716163200,
    "Total Posts Contracted": 5,
    "Total Posts Delivered": 5,
    "Bio Link Verified": True,
    "Hashtags Verified": True,
    "Paid Usage": True,
    "Performance Updated": True,
    "Payment Trigger": "Invoice Received",   # ★ Plan B 触发
}

# CT004: 三项失败 + Payment Trigger = Invoice Received
CT004 = {
    "record_id": "recvi5N0H8ZiNB",
    "Name of Entity": "harperwellness LLC",
    "Campaign": "PulseRope Holiday Push",
    "Contract Amount (USD)": 900,
    "Invoice Amount (USD)": 900,
    "GL Number": "GL-1004",
    "Payment Due Date": 1717200000,
    "Total Posts Contracted": 2,
    "Total Posts Delivered": 0,
    "Bio Link Verified": False,
    "Hashtags Verified": True,
    "Paid Usage": True,
    "Performance Updated": False,
    "Payment Trigger": "Invoice Received",
}


if __name__ == "__main__":
    print("="*60)
    print("🎯 Plan B 路由测试：Payment Trigger = Invoice Received")
    print("="*60)

    # 路由测试
    trigger_event = {"Payment Trigger": "Invoice Received"}
    route = route_scene(trigger_event)
    print(f"\n路由结果: route_scene({trigger_event}) → '{route}'")
    assert route == "act5", f"Expected 'act5', got '{route}'"
    print("✅ 路由正确")

    print("\n" + "="*60)
    print("🟢 场景一：CT002 - 五项全绿（应生成预填）")
    print("="*60)
    execute_act5(CT002)

    print("\n\n" + "="*60)
    print("🔴 场景二：CT004 - 三项失败（应显示失败项）")
    print("="*60)
    execute_act5(CT004)

    print("\n" + "="*60)
    print("✅ 端到端测试完成")
    print("="*60)
