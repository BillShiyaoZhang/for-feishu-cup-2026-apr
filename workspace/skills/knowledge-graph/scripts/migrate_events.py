#!/usr/bin/env python3
"""
migrate_events.py — Migrate daily memory logs to event KG files.

This script reads the daily memory files and creates corresponding event nodes
in the appropriate graph-events-YYYY-QN.trig files.

Usage:
    python migrate_events.py --dry-run    # Show what would be created
    python migrate_events.py --execute    # Actually create events
"""
import argparse
import datetime
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
KG_DIR = SCRIPT_DIR.parent / "kg"
MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"

PYTHON = Path.home() / ".openclaw/workspace/.venv/bin/python"


def get_quarter(date_str: str) -> str:
    """Return YYYY-QN for a date string like 2026-04-10."""
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    month = dt.month
    year = dt.year
    q = (month - 1) // 3 + 1
    return f"{year}-Q{q}"


def get_event_graph(quarter: str) -> Path:
    """Return the graph file path for a given quarter."""
    return KG_DIR / f"graph-events-{quarter}.trig"


def escape_id(s: str) -> str:
    """Create a valid KG ID from a string."""
    return s.lower().replace(" ", "-").replace("_", "-")


# All events to migrate
EVENTS = [
    # Q1 Events (March 2026)
    {
        "id": "xjtlu-symposium-day1",
        "name": "XJTLU Postgraduate Research Symposium Day 1",
        "description": "Bill served as Student Chair for XJTLU Postgraduate Research Symposium. Tasks: collect PPTs from attendees, supervise venue logistics, coordinate with volunteers.",
        "event_type": "meeting",
        "date": "2026-03-19",
        "time": "2026-03-19T08:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-03-19.md"),
    },
    {
        "id": "xjtlu-symposium-day2",
        "name": "XJTLU Postgraduate Research Symposium Day 2",
        "description": "Bill served as Student Chair for Day 2 of XJTLU Postgraduate Research Symposium.",
        "event_type": "meeting",
        "date": "2026-03-20",
        "time": "2026-03-20T08:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-03-20.md"),
    },
    {
        "id": "equipment-testing-day2",
        "name": "Symposium Equipment Testing Day 2",
        "description": "Symposium equipment testing day 2. Location: all meeting rooms. Time: 13:00-17:00. Need to bring laptop.",
        "event_type": "task",
        "date": "2026-03-13",
        "time": "2026-03-13T13:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-03-13.md"),
    },
    {
        "id": "fun-workshop-podcast-discussion",
        "name": "Fun Workshop Podcast Project Discussion",
        "description": "Bill discussed Fun Workshop podcast project: interview-style podcast, topic proposal → invite speaker → discussion, monetization via sponsors.",
        "event_type": "meeting",
        "date": "2026-03-11",
        "time": "2026-03-11T14:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-03-11.md"),
    },

    # Q2 Events (April 2026)
    {
        "id": "g3282-zhengzhou-to-taicang",
        "name": "G3282 郑州东→太仓",
        "description": "Bill took G3282 from 郑州东 to 太仓. Departure 10:16, arrival 15:42. Passenger: 张世尧 (Bill). Car 01, Seat 08D, 一等座.",
        "event_type": "travel",
        "date": "2026-04-09",
        "time": "2026-04-09T10:16:00+08:00",
        "agents": ["kg:person-bill"],
        "location": "郑州东站",
        "source": str(MEMORY_DIR / "2026-04-09.md"),
    },
    {
        "id": "meeting-qin-yidan",
        "name": "Meeting with 秦一丹",
        "description": "Bill met 秦一丹 at 太仓学校 to discuss event collaboration. 16:00-17:00.",
        "event_type": "meeting",
        "date": "2026-04-09",
        "time": "2026-04-09T16:00:00+08:00",
        "agents": ["kg:person-bill", "kg:person-qin-yidan"],
        "location": "kg:location-taicang-school",
        "source": str(MEMORY_DIR / "2026-04-09.md"),
    },
    {
        "id": "iot105tc-tutorial",
        "name": "IOT105TC Tutorial",
        "description": "IOT105TC tutorial at BC-3001. 11:00.",
        "event_type": "task",
        "date": "2026-04-10",
        "time": "2026-04-10T11:00:00+08:00",
        "agents": ["kg:person-bill"],
        "location": "BC-3001",
        "source": str(MEMORY_DIR / "2026-04-10.md"),
    },
    {
        "id": "arduino-handoff-oswaldo",
        "name": "Arduino Kit Handoff to Oswaldo",
        "description": "Bill transported Arduino kits from Lab E-4002 to classroom for Oswaldo. Oswaldo arrived 10:45-10:50 to pick up.",
        "event_type": "task",
        "date": "2026-04-10",
        "time": "2026-04-10T10:45:00+08:00",
        "agents": ["kg:person-bill", "kg:person-oswaldo"],
        "location": "kg:location-lab-e4002",
        "source": str(MEMORY_DIR / "2026-04-10.md"),
    },
    {
        "id": "cognitive-performance-music-session-1",
        "name": "Cognitive Performance Music Session III - Session 1",
        "description": "Cognitive Performance Music Session III at SIP Campus, CB117W. 35-min sound experience. Limited to 50 participants.",
        "event_type": "social",
        "date": "2026-04-04",
        "time": "2026-04-04T18:00:00+08:00",
        "agents": ["kg:person-bill"],
        "location": "SIP Campus, CB117W",
        "source": str(MEMORY_DIR / "2026-03-31.md"),
    },
    {
        "id": "cognitive-performance-music-session-2",
        "name": "Cognitive Performance Music Session III - Session 2",
        "description": "Cognitive Performance Music Session III at XEC Campus, G-1006. 35-min sound experience. Limited to 50 participants.",
        "event_type": "social",
        "date": "2026-04-11",
        "time": "2026-04-11T18:00:00+08:00",
        "agents": ["kg:person-bill"],
        "location": "XEC Campus, G-1006",
        "source": str(MEMORY_DIR / "2026-03-31.md"),
    },
    {
        "id": "fun-workshop-apr14",
        "name": "Fun Workshop",
        "description": "Fun Workshop (bi-weekly Tuesday 16:00-18:00, Tencent Meeting). Topic to be confirmed.",
        "event_type": "social",
        "date": "2026-04-14",
        "time": "2026-04-14T16:00:00+08:00",
        "agents": ["kg:person-bill"],
        "location": "Tencent Meeting",
        "source": str(MEMORY_DIR / "2026-03-31.md"),
    },
    {
        "id": "system-memory-sync",
        "name": "Memory Sync",
        "description": "Scheduled memory sync. Processed 4 new sessions. Updated MEMORY.md with Cognitive Performance Music Session III and Fun Workshop schedule.",
        "event_type": "system",
        "date": "2026-03-31",
        "time": "2026-03-31T20:00:00+08:00",
        "agents": ["kg:agent-memory-manager"],
        "source": str(MEMORY_DIR / "2026-03-31.md"),
    },
    {
        "id": "system-planner-removed",
        "name": "Planner Agent Removed",
        "description": "Bill removed the planner agent. Calendar skill migrated to main agent (Claw). Morning Briefing now runs as Claw isolated session. Identity returned to Claw.",
        "event_type": "system",
        "date": "2026-04-01",
        "time": "2026-04-01T10:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-04-01.md"),
    },
    {
        "id": "system-ontology-debug",
        "name": "Ontology Skill Debug",
        "description": "Bill debugged ontology skill: fixed kg:gateway/main syntax error (/) and xsd:anyURI validation issue. Created .venv with rdflib + pyshacl. SHACL validation now passes.",
        "event_type": "system",
        "date": "2026-04-01",
        "time": "2026-04-01T14:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-04-01.md"),
    },
    {
        "id": "system-customer-manager-removed",
        "name": "customer-manager Agent Removed",
        "description": "Bill completely removed customer-manager agent. Cleaned up graph.trig entries: kg:memory-feishu-customer-manager, kg:agent-customer-manager, kg:binding-customer-manager-feishu. Cleared openclaw.json channel config.",
        "event_type": "system",
        "date": "2026-04-10",
        "time": "2026-04-10T09:00:00+08:00",
        "agents": ["kg:person-bill"],
        "source": str(MEMORY_DIR / "2026-04-10.md"),
    },
]


def build_command(event: dict) -> list:
    """Build the manage_entity.py command for an event."""
    quarter = get_quarter(event["date"])
    graph = get_event_graph(quarter)

    cmd = [
        str(PYTHON),
        str(SCRIPT_DIR / "manage_entity.py"),
        "--graph", str(graph),
        "--type", "event",
        "--id", event["id"],
        "--name", event["name"],
        "--description", event["description"],
        "--event-type", event["event_type"],
        "--event-time", event["time"],
        "--source-file", event["source"],
    ]

    for agent in event.get("agents", []):
        cmd += ["--agent", agent]

    if event.get("location"):
        cmd += ["--location", event["location"]]

    return cmd


def main():
    parser = argparse.ArgumentParser(description="Migrate daily memory logs to event KG.")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    parser.add_argument("--execute", action="store_true", help="Actually execute migrations")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Use --dry-run to preview or --execute to run migrations.")
        sys.exit(1)

    for ev in EVENTS:
        cmd = build_command(ev)
        quarter = get_quarter(ev["date"])
        print(f"[{quarter}] {ev['id']}")
        print(f"  {ev['name']}")
        print(f"  {ev['time']}")
        if args.dry_run:
            import shlex
            print(f"  CMD: {' '.join(shlex.quote(str(c)) for c in cmd)}")
        elif args.execute:
            import subprocess
            print(f"  Running...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Done")
            else:
                print(f"  ❌ Failed: {result.stderr}")
        print()


if __name__ == "__main__":
    main()
