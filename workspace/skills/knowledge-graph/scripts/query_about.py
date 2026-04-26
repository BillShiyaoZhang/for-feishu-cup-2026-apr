#!/usr/bin/env python3
"""
query_about.py — Unified KG query for questions about a person.

Usage:
    python query_about.py "Bill"
    python query_about.py "Bill 的行程"
    python query_about.py "Bill 认识谁"

Replaces file-based memory_search with KG-native queries.
Searches both Core KG (graph.trig) and Event KG (graph-events-*.trig).
"""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).parent.resolve()
KG_DIR = SCRIPT_DIR.parent / "kg"

# ── Load shared modules ────────────────────────────────────────────────────────
sys.path.insert(0, str(SCRIPT_DIR))

# Import helpers from existing scripts (reuse, don't copy)
import query_entity   # for get_all_entities, keyword_score, semantic_search
import query_events   # for find_event_files, load_graphs, format_event

from rdflib import ConjunctiveGraph, Namespace, RDF, URIRef
from rdflib.namespace import RDF

NAMESPACES = {
    "openclaw": "urn:openclaw:ontology#",
    "kg":       "urn:openclaw:kg:",
    "foaf":     "http://xmlns.com/foaf/0.1/",
    "event":    "http://purl.org/NET/c4dm/event.owl#",
    "xsd":      "http://www.w3.org/2001/XMLSchema#",
}

# ── Scoring helpers ────────────────────────────────────────────────────────────

def _semantic_score_fallback(query: str, text: str) -> float:
    """Fallback sequence matching when sentence_transformers unavailable."""
    import difflib
    seq = difflib.SequenceMatcher(None, query.lower(), text.lower())
    return seq.ratio()


def score_entity(entity: dict, query: str) -> float:
    """0.4 keyword + 0.6 semantic (same as query_entity.py)."""
    text = entity.get("text", "").lower()
    ks = query_entity.keyword_score(query.lower(), text)
    ss = _semantic_score_fallback(query.lower(), text)
    return 0.4 * ks + 0.6 * ss


def score_event(event: dict, query: str) -> float:
    """Score an event by name + description text."""
    text = " ".join([
        event.get("name", ""),
        event.get("description", "")
    ]).lower()
    ks = query_entity.keyword_score(query.lower(), text)
    ss = _semantic_score_fallback(query.lower(), text)
    return 0.4 * ks + 0.6 * ss


# ── Core KG search ────────────────────────────────────────────────────────────

def search_core_kg(query: str, limit: int = 10):
    """Search Core KG (graph.trig) for entities matching query.

    Now ontology-aware: query_entity.get_all_entities() uses canonical
    name/description properties per ontology type definition
    (foaf:name for foaf:Person, openclaw:hasName for openclaw:* types).
    """
    graph_path = KG_DIR / "graph.trig"
    if not graph_path.exists():
        return []

    g = ConjunctiveGraph()
    g.parse(str(graph_path), format="trig")

    entities = query_entity.get_all_entities(g)

    # Score each entity
    for e in entities:
        e["score"] = score_entity(e, query)

    entities.sort(key=lambda x: x["score"], reverse=True)
    return entities[:limit]


# ── Event KG search ────────────────────────────────────────────────────────────

def search_event_kg(query: str, person_uri: str = None, limit: int = 20,
                   event_type: str = None, sort_by_time: bool = False):
    """Search Event KG for events.

    Args:
        query: Search query for scoring (used when sort_by_time=False)
        person_uri: Filter by person agent
        limit: Max results
        event_type: Filter by event type (e.g. 'travel')
        sort_by_time: If True, sort by time instead of score (for travel queries)
    """
    # Load all event files
    all_files = list(KG_DIR.glob("graph-events-*.trig"))
    if not all_files:
        return []

    g = query_events.load_graphs(all_files)

    OPENCLAW = Namespace(NAMESPACES["openclaw"])
    EVENT = Namespace(NAMESPACES["event"])
    KG = Namespace(NAMESPACES["kg"])

    # Find all events
    events = list(g.subjects(RDF.type, EVENT.Event))

    results = []
    for ev in events:
        # Filter by person if specified
        if person_uri:
            person_key = person_uri.replace("kg:", "")
            person_node = KG[person_key]
            if not (ev, EVENT.agent, person_node) in g:
                continue

        details = query_events.format_event(ev, g, show_agents=False)

        # Filter by event type
        if event_type and details.get("type") != event_type:
            continue

        details["score"] = score_event(details, query)
        results.append(details)

    if sort_by_time:
        results.sort(key=lambda x: x.get("time", ""), reverse=True)
    else:
        results.sort(key=lambda x: x["score"], reverse=True)

    return results[:limit]


# ── Special query patterns ─────────────────────────────────────────────────────

TRIP_KEYWORDS = {"行程", "trip", "travel", "火车", "飞机", "高铁"}
PEOPLE_KEYWORDS = {"认识谁", "people", "friends", "朋友", "联系人"}
LOCATION_KEYWORDS = {"地点", "locations", "地方", "在哪"}


def detect_mode(query: str) -> tuple[str, str]:
    """Detect special query mode and modified query.

    Returns (mode, modified_query).
    mode: 'travel' | 'people' | 'location' | 'all'
    """
    q_lower = query.lower().strip()
    for kw in TRIP_KEYWORDS:
        if kw in q_lower:
            return "travel", query
    for kw in PEOPLE_KEYWORDS:
        if kw in q_lower:
            return "people", query
    for kw in LOCATION_KEYWORDS:
        if kw in q_lower:
            return "location", query
    return "all", query


# ── Output formatters ──────────────────────────────────────────────────────────

def print_entities(entities: list, label: str):
    """Print a list of entities with score."""
    if not entities:
        return
    print(f"\n{label} ({len(entities)} results)\n")
    for i, e in enumerate(entities, 1):
        etype = e.get("type", "unknown")
        score = e.get("score", 0)
        name = e.get("name", "unnamed")
        desc = e.get("description", "")
        uri = e.get("uri", "")
        print(f"{i}. {name} ({etype}) — score: {score:.3f}")
        if desc:
            print(f"   {desc}")
        print()


def print_events(events: list, label: str):
    """Print a list of events with time and type."""
    if not events:
        return
    print(f"\n{label} ({len(events)} results)\n")
    for i, ev in enumerate(events, 1):
        name = ev.get("name", "unnamed event")
        evtype = ev.get("type", "")
        time_str = ev.get("time", "")
        desc = ev.get("description", "")
        score = ev.get("score", 0)

        # Format time
        if time_str:
            if "T" in time_str:
                time_str = time_str.split("T")[0]

        print(f"{i}. {name} — {evtype} — {time_str} (score: {score:.3f})")
        if desc:
            print(f"   {desc}")
        print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified KG query for questions about a person.")
    parser.add_argument("query", type=str, help="Search query (e.g. 'Bill', 'Bill 的行程')")
    parser.add_argument("--limit", type=int, default=10, help="Max results per category")
    parser.add_argument("--person", type=str, default=None, help="Person KG URI (e.g. kg:person-bill)")
    parser.add_argument("--mode", type=str, default=None,
                        choices=["all", "travel", "people", "location"],
                        help="Force a specific query mode")
    args = parser.parse_args()

    query = args.query
    limit = args.limit
    person_uri = args.person or "kg:person-bill"  # default to Bill

    # Detect mode
    mode, modified_query = detect_mode(query) if not args.mode else (args.mode, query)

    print(f"=== 关于 \"{query}\" 的回答 ===")
    print(f"(mode: {mode}, person: {person_uri})\n")

    # Search Core KG
    entities = search_core_kg(modified_query, limit=limit)

    # Separate entities by type (use 'in' check since types are 'foaf:Person', 'openclaw:Location', etc.)
    people    = [e for e in entities if "Person"   in e.get("type", "")]
    locations = [e for e in entities if "Location" in e.get("type", "")]
    skills    = [e for e in entities if "Skill"    in e.get("type", "")]

    # Search Event KG
    events = search_event_kg(
        modified_query,
        person_uri=person_uri,
        limit=limit,
        event_type="travel" if mode == "travel" else None,
        sort_by_time=(mode == "travel")
    )

    # Output
    if mode == "all":
        print_entities(people, "👤 人物")
        print_entities(locations, "📍 地点")
        print_entities(skills, "🛠️ 技能")
        print_events(events, "📅 事件")

    elif mode == "travel":
        print_events(events, "🚄 行程")

    elif mode == "people":
        print_entities(people, "👤 人物")
        # Also find people from event agents
        all_events = search_event_kg(modified_query, person_uri=person_uri, limit=limit)
        agent_map = {}
        for ev in all_events:
            for a in ev.get("agents", []):
                if "person" in a.lower():
                    agent_map[a] = ev.get("name", "")
        # Show distinct person URIs from events
        person_uris_in_events = [a for a in agent_map.keys() if a != f"urn:{person_uri}"]
        if person_uris_in_events:
            print(f"\n👥 相关人物（从事件中发现）\n")
            for i, pu in enumerate(person_uris_in_events[:limit], 1):
                name = pu.replace("urn:openclaw:kg:", "")
                print(f"{i}. {name}")

    elif mode == "location":
        print_entities(locations, "📍 地点")

    if not any([people, locations, skills, events]):
        print("没有找到相关内容。试试更具体的查询？")


if __name__ == "__main__":
    main()
