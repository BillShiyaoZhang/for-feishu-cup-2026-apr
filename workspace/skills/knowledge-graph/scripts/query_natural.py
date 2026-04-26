#!/usr/bin/env python3
"""
query_natural.py — Natural language query to structured KG query parameters.

Architecture:
  1. Dynamically loads schema from ontology files (core.ttl, shapes.ttl)
     and KG data files (graph.trig, graph-events-*.trig)
  2. Provides ground-truth schema context so the LLM knows what types,
     properties, and enum values actually exist — prevents hallucination
  3. Outputs structured JSON of query parameters

This script does NOT call the LLM API — it provides schema context that
the main agent (which IS an LLM) uses to make grounded decisions.

Usage:
    python query_natural.py "Bill 4月份去过哪些地方"
    python query_natural.py "我最近见过哪些朋友"
    python query_natural.py "秦一丹是谁"
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent.resolve()
KG_DIR = SCRIPT_DIR.parent / "kg"
ONTOLOGY_DIR = SCRIPT_DIR.parent.parent / "ontology" / "ontology"


# ── Dynamic Schema Loader ──────────────────────────────────────────────────────

def load_schema_from_ontology() -> dict:
    """
    Parse core.ttl to extract all class and property definitions.
    This is the ground-truth schema — the source of all field names,
    domains, ranges, and enum values.
    """
    core_ttl = ONTOLOGY_DIR / "core.ttl"
    if not core_ttl.exists():
        return {}

    content = core_ttl.read_text()
    classes = _extract_classes(content)
    properties = _extract_properties(content)
    enums = _extract_enums(content)

    return {
        "classes": classes,
        "properties": properties,
        "enums": enums,
    }


def _extract_classes(content: str) -> dict:
    """Extract owl:Class definitions with their rdfs:comment."""
    classes = {}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "a owl:Class" in line or "a rdfs:Class" in line:
            # Get the class ID from the line before
            class_id = lines[i - 1].strip().rstrip(":").strip()
            # Collect comment
            comment_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("rdfs:comment"):
                comment_lines.append(lines[j].strip())
                j += 1
            comment = " ".join(c.replace("rdfs:comment", "").strip(' """').strip() for c in comment_lines)
            classes[class_id] = {"comment": comment, "properties": []}
        i += 1
    return classes


def _extract_properties(content: str) -> dict:
    """Extract owl:DatatypeProperty and owl:ObjectProperty definitions."""
    properties = {}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "a owl:DatatypeProperty" in line or "a owl:ObjectProperty" in line:
            prop_id = lines[i - 1].strip().rstrip(":").strip()
            prop_type = "DatatypeProperty" if "DatatypeProperty" in line else "ObjectProperty"
            domain = None
            range_ = None
            comment = None
            j = i + 1
            while j < len(lines):
                l = lines[j].strip()
                if l.startswith("rdfs:domain"):
                    domain = l.split()[-1].rstrip(";").strip()
                elif l.startswith("rdfs:range"):
                    range_ = l.split()[-1].rstrip(";").strip()
                elif l.startswith("rdfs:comment"):
                    comment = l.replace("rdfs:comment", "").strip(' """').strip()
                elif l.startswith("a ") or l.startswith("#") or l.startswith("openclaw:") or l.startswith("foaf:") or l.startswith("event:"):
                    break
                j += 1
            properties[prop_id] = {
                "type": prop_type,
                "domain": domain,
                "range": range_,
                "comment": comment
            }
        i += 1
    return properties


def _extract_enums(content: str) -> dict:
    """
    Extract owl:oneOf enumerations.
    These define controlled vocabularies (e.g. EventTypeValue).
    """
    enums = {}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "owl:oneOf" in line:
            # Get the class ID from preceding lines
            class_id = None
            j = i - 1
            while j >= 0 and class_id is None:
                l = lines[j].strip()
                if l.startswith("openclaw:") or l.startswith("foaf:") or l.startswith("event:"):
                    class_id = l.rstrip(":").strip()
                    break
                j -= 1
            # Collect values
            values = []
            j = i + 1
            while j < len(lines):
                l = lines[j].strip().rstrip(") ;").strip()
                if l.startswith('"'):
                    values.append(l.strip('"').strip())
                elif l == ".":
                    break
                j += 1
            if class_id:
                enums[class_id] = {"values": values}
        i += 1
    return enums


def get_kg_id_patterns(kg_graph_path: Path) -> dict:
    """
    Discover kg: ID patterns from actual KG data.
    Reads graph.trig to find all entity type prefixes in use.
    """
    if not kg_graph_path.exists():
        return {}

    content = kg_graph_path.read_text()
    patterns = {}

    # Find all kg:person-*, kg:location-*, kg:agent-*, kg:skill-* references
    for match in re.finditer(r'(kg:(?:person|location|agent|skill|event)-[\w-]+)', content):
        full_id = match.group(1)
        prefix = "-".join(full_id.split("-")[:-1])  # kg:person
        suffix = full_id.split("-")[-1]  # bill
        if prefix not in patterns:
            patterns[prefix] = {"example": full_id, "count": 1}
        else:
            patterns[prefix]["count"] = patterns[prefix].get("count", 1) + 1

    return patterns


# ── Event Type Discovery ──────────────────────────────────────────────────────

def discover_event_types() -> list:
    """
    Read all graph-events-*.trig files to find all eventType values
    currently in use. This is the empirical enum — what we actually use.
    """
    event_types = set()
    for trig_file in KG_DIR.glob("graph-events-*.trig"):
        content = trig_file.read_text()
        for match in re.finditer(r'openclaw:eventType\s+"([^"]+)"', content):
            event_types.add(match.group(1))
    return sorted(event_types)


# ── Build Schema Context ──────────────────────────────────────────────────────

def build_schema_context() -> dict:
    """
    Construct the full schema context from ontology + KG.
    This is what the agent uses to construct valid queries without guessing.
    """
    ontology_schema = load_schema_from_ontology()
    enums = ontology_schema.get("enums", {})
    properties = ontology_schema.get("properties", {})
    classes = ontology_schema.get("classes", {})
    kg_patterns = get_kg_id_patterns(KG_DIR / "graph.trig")
    active_event_types = discover_event_types()

    # Derive event types: prefer ontology enum, fallback to empirical discovery
    event_type_enum = enums.get("openclaw:EventTypeValue", {}).get("values", [])
    if not event_type_enum:
        event_type_enum = active_event_types

    # Build property reference for event-related queries
    event_properties = {}
    for prop_id, prop_info in properties.items():
        if prop_info.get("domain") in ("event:Event", "owl:Thing") or "event" in prop_id.lower():
            event_properties[prop_id] = prop_info

    # Build entity-related properties
    person_properties = {}
    for prop_id, prop_info in properties.items():
        if "Person" in str(prop_info.get("domain", "")) or "person" in prop_id.lower():
            person_properties[prop_id] = prop_info

    return {
        "event_types": {
            "source": "ontology:openclaw:EventTypeValue.owl:oneOf",
            "enum": event_type_enum,
            "active_in_kg": active_event_types,
            "description": "openclaw:eventType — category of an event:Event"
        },
        "query_targets": {
            "events": {
                "description": "Query graph-events-*.trig for time-stamped events",
                "kg_file_pattern": "graph-events-YYYY-QN.trig",
                "required_props": ["event:time", "openclaw:eventType"],
                "optional_props": ["openclaw:hasName", "openclaw:hasDescription", "event:agent", "openclaw:eventLocation"],
                "filters": ["time_from", "time_to", "event_types", "agents", "location_text", "keywords"],
                "sort_options": ["time_desc", "time_asc", "relevance"],
            },
            "entities": {
                "description": "Query graph.trig for person/location/agent/skill/concept",
                "kg_file": "graph.trig",
                "entity_types": list(kg_patterns.keys()),
                "kg_id_examples": kg_patterns,
                "filters": ["entity_type", "keywords", "kg_id"],
            }
        },
        "properties": {
            # Event properties
            "event_name": "openclaw:hasName",
            "event_description": "openclaw:hasDescription",
            "event_type": "openclaw:eventType",
            "event_time": "event:time",
            "event_agent": "event:agent",
            "event_location": "openclaw:eventLocation",
            # Person properties
            "person_name": "foaf:name",
            "person_given_name": "foaf:givenName",
            "person_note": "openclaw:note",
        },
        "namespaces": {
            "openclaw": "urn:openclaw:ontology#",
            "kg": "urn:openclaw:kg:",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "event": "http://purl.org/NET/c4dm/event.owl#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        },
        "ontology_classes": classes,
        "property_count": len(properties),
        "enum_count": len(enums),
    }


# ── Intent Parser ─────────────────────────────────────────────────────────────

def parse_natural_query(query: str) -> dict:
    """
    Parse a natural language query into structured KG query parameters.
    This is rule-based + keyword-driven — a grounded fallback.
    For full LLM-powered parsing, the main agent should use build_schema_context()
    output as a schema guide and interpret the query itself.
    """
    q = query.strip()
    result = {
        "query_target": "events",
        "filters": {
            "agents": [],
            "event_types": [],
            "time_from": None,
            "time_to": None,
            "keywords": [],
            "location_text": None,
        },
        "requires_core_kg": False,
        "requires_event_kg": True,
        "sort": "time_desc",
        "limit": 20,
    }

    # Detect entity query (person lookup)
    if any(kw in q for kw in ["是谁", "查人", "查查", "认识", "朋友", "人"]):
        result["query_target"] = "entities"
        result["entity_type"] = "person"
        result["requires_core_kg"] = True
        result["requires_event_kg"] = False
        result["filters"]["keywords"] = _extract_keywords(q)
        return result

    # Detect location query
    if any(kw in q for kw in ["去过哪", "在哪儿", "地点", "位置"]):
        result["filters"]["event_types"] = ["travel", "meeting", "social"]

    # Detect time range
    time_from, time_to = _extract_time_range(q)
    result["filters"]["time_from"] = time_from
    result["filters"]["time_to"] = time_to

    # Detect event types by keyword
    type_keywords = {
        "travel": ["火车", "飞机", "高铁", "行程", "去", "回", "出发", "到达", "航班", "车次"],
        "meeting": ["会议", "见面", "会面", "讨论", "聊", "谈", "meeting", "约"],
        "social": ["聚会", "活动", "social", "咖啡", "吃饭", " dinner", "lunch", "聚", "玩"],
        "task": ["任务", "todo", "task", "工作", "作业", "报告", "填写", "review"],
        "system": ["系统", "配置", "system", "更新", "架构", "部署"],
    }
    found_types = []
    for etype, keywords in type_keywords.items():
        if any(kw in q.lower() for kw in keywords):
            found_types.append(etype)
    if found_types:
        result["filters"]["event_types"] = found_types

    # Bill as agent
    if "我" in q or "Bill" in q or "世尧" in q:
        result["filters"]["agents"] = ["kg:person-bill"]

    # Location extraction
    location = _extract_location(q)
    if location:
        result["filters"]["location_text"] = location

    # Keywords
    result["filters"]["keywords"] = _extract_keywords(q)

    # Sort
    if any(kw in q for kw in ["最近", "latest", "最近一次"]):
        result["sort"] = "time_desc"

    return result


def _extract_time_range(q: str) -> tuple:
    """Extract time range from Chinese natural language query."""
    time_from = None
    time_to = None

    # "4月份" / "四月"
    month_match = re.search(r"(?:2026[年]?)?([12]?[1-9]|10|11|12)?月", q)
    if month_match and month_match.group(1):
        month = int(month_match.group(1))
        year = 2026
        time_from = f"{year}-{month:02d}-01"
        days_in_month = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
        time_to = f"{year}-{month:02d}-{days_in_month[month]:02d}"

    # "最近N天/周"
    day_match = re.search(r"最近\s*(\d+)\s*天", q)
    if day_match:
        days = int(day_match.group(1))
        today = datetime.now()
        time_to = today.strftime("%Y-%m-%d")
        time_from = (today - timedelta(days=days)).strftime("%Y-%m-%d")

    # "最近" alone → last 30 days
    if "最近" in q and not (time_from or time_to):
        today = datetime.now()
        time_to = today.strftime("%Y-%m-%d")
        time_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    return time_from, time_to


def _extract_location(q: str) -> str:
    """Extract location references from query."""
    known_locations = ["太仓", "上海", "重庆", "郑州", "虹桥", "西浦", "XJTLU",
                       "Lab", "E-4002", "虹桥机场", "浦东", "学校", "教室", " classroom"]
    for loc in known_locations:
        if loc in q:
            return loc
    return None


def _extract_keywords(q: str) -> list:
    """Extract meaningful keywords (excluding stop words)."""
    stop_words = {"的", "是", "了", "在", "和", "与", "或", "有没有", "吗", "呢",
                  "我", "最近", "去过", "见过", "认识", "Bill", "什么", "哪些",
                  "一个", "你", "他", "她", "请", "一下", "能", "可以"}
    words = q.replace("?", "").replace("？", "").replace("，", " ").replace(",", " ").split()
    return [w for w in words if w not in stop_words and len(w) > 1]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: query_natural.py <natural_language_query>", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    schema_context = build_schema_context()
    parsed_params = parse_natural_query(query)

    output = {
        "query": query,
        "schema_context": schema_context,
        "parsed_params": parsed_params,
        "instructions": (
            "Use parsed_params to call query_events.py or query_entity.py. "
            "schema_context contains ground-truth field names (from ontology), "
            "enum values (from openclaw:EventTypeValue.owl:oneOf), and kg: ID "
            "patterns (from graph.trig). "
            "IMPORTANT: Only use field names and enum values from schema_context. "
            "Do NOT invent property names or event type values. "
            "If a filter needs a kg_id (e.g. agent), use the kg_id_patterns "
            "from schema_context.query_targets.entities.kg_id_examples."
        )
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
