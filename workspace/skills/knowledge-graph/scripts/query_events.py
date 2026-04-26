#!/usr/bin/env python3
"""
query_events.py — Query events from partitioned event graph files.

Usage:
    # Query all events in a time range
    python query_events.py --from 2026-04-01 --to 2026-04-30

    # Query events for a specific person
    python query_events.py --person kg:person-bill --from 2026-03-01 --to 2026-04-30

    # Query events by type
    python query_events.py --event-type travel --from 2026-01-01 --to 2026-12-31

    # Show agents/participants for each event
    python query_events.py --from 2026-04-01 --to 2026-04-30 --show-agents

    # Verbose output with all details
    python query_events.py --from 2026-04-01 --to 2026-04-30 --verbose
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef
from rdflib.namespace import RDF

SCRIPT_DIR = Path(__file__).parent.resolve()
KG_DIR = SCRIPT_DIR.parent / "kg"

NAMESPACES = {
    "openclaw": "urn:openclaw:ontology#",
    "kg":       "urn:openclaw:kg:",
    "foaf":     "http://xmlns.com/foaf/0.1/",
    "event":    "http://purl.org/NET/c4dm/event.owl#",
    "xsd":      "http://www.w3.org/2001/XMLSchema#",
}


def get_quarter(date_str: str) -> str:
    """Return YYYY-QN for a date string like 2026-04-10."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    month = dt.month
    year = dt.year
    q = (month - 1) // 3 + 1
    return f"{year}-Q{q}"


def extract_quarter(filename: str) -> str:
    """Extract YYYY-QN from a filename like graph-events-2026-Q2.trig."""
    import re
    m = re.search(r'(\d{4}-Q[1-4])', filename)
    if m:
        return m.group(1)
    return None


def find_event_files(from_date: str, to_date: str) -> list[Path]:
    """Find all event graph files that could contain events in the given range."""
    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")

    from_q = get_quarter(from_date)
    to_q = get_quarter(to_date)

    files = []
    for f in KG_DIR.glob("graph-events-*.trig"):
        quarter = extract_quarter(f.name)
        if quarter:
            files.append((quarter, f))

    # Filter to quarters in range
    from_q_num = int(from_q.split("-Q")[0]) * 10 + int(from_q.split("-Q")[1])
    to_q_num = int(to_q.split("-Q")[0]) * 10 + int(to_q.split("-Q")[1])

    filtered = []
    for q, f in files:
        try:
            year = int(q.split("-Q")[0])
            quarter = int(q.split("-Q")[1])
            q_num = year * 10 + quarter
            if q_num >= from_q_num and q_num <= to_q_num:
                filtered.append(f)
        except (ValueError, IndexError):
            continue

    return sorted(filtered, key=lambda p: p.name)


def load_graphs(file_paths: list[Path]) -> ConjunctiveGraph:
    """Load multiple event graph files into a single ConjunctiveGraph."""
    g = ConjunctiveGraph()
    NS = {k: Namespace(v) for k, v in NAMESPACES.items()}
    for prefix, ns in NS.items():
        g.bind(prefix, ns)

    for fp in file_paths:
        g.parse(str(fp), format="trig")
    return g


def format_event(event_uri: URIRef, g: ConjunctiveGraph, show_agents: bool = False) -> dict:
    """Extract event details as a dict."""
    OPENCLAW = Namespace(NAMESPACES["openclaw"])
    EVENT = Namespace(NAMESPACES["event"])

    result = {
        "uri": str(event_uri),
        "id": str(event_uri).replace("urn:openclaw:kg:", ""),
    }

    # Name
    name = g.value(event_uri, OPENCLAW.hasName)
    if name:
        result["name"] = str(name)

    # Description
    desc = g.value(event_uri, OPENCLAW.hasDescription)
    if desc:
        result["description"] = str(desc)

    # Event type
    evtype = g.value(event_uri, OPENCLAW.eventType)
    if evtype:
        result["type"] = str(evtype)

    # Time
    evtime = g.value(event_uri, EVENT.time)
    if evtime:
        result["time"] = str(evtime)

    # Source file
    source = g.value(event_uri, OPENCLAW.sourceFile)
    if source:
        result["source"] = str(source)

    # Location
    loc = g.value(event_uri, OPENCLAW.eventLocation)
    if loc:
        result["location"] = str(loc)

    # Agents
    if show_agents:
        agents = list(g.objects(event_uri, EVENT.agent))
        result["agents"] = [str(a) for a in agents]

    return result


def query_events(
    from_date: str = None,
    to_date: str = None,
    person_uri: str = None,
    event_type: str = None,
    keywords: list = None,
    show_agents: bool = False,
    verbose: bool = False,
):
    """Main query logic."""
    files = find_event_files(from_date, to_date) if from_date else list(KG_DIR.glob("graph-events-*.trig"))

    if not files:
        print("No event files found.")
        return

    g = load_graphs(files)

    OPENCLAW = Namespace(NAMESPACES["openclaw"])
    EVENT = Namespace(NAMESPACES["event"])
    KG = Namespace(NAMESPACES["kg"])

    # SPARQL-like filtering in Python for simplicity
    events = list(g.subjects(RDF.type, EVENT.Event))

    results = []
    for ev in events:
        # Filter by person
        if person_uri:
            person_node = KG[person_uri.replace("kg:", "")] if person_uri.startswith("kg:") else URIRef(person_uri)
            if not (ev, EVENT.agent, person_node) in g:
                continue

        # Filter by type
        if event_type:
            evtype = g.value(ev, OPENCLAW.eventType)
            if not evtype or str(evtype) != event_type:
                continue

        # Filter by time range
        if from_date and to_date:
            evtime = g.value(ev, EVENT.time)
            if evtime:
                ev_str = str(evtime)
                # Handle xsd:dateTime format
                if "T" in ev_str:
                    ev_date = ev_str.split("T")[0]
                else:
                    ev_date = ev_str
                if ev_date < from_date or ev_date > to_date:
                    continue

        # Filter by keywords (name or description)
        if keywords:
            name = g.value(ev, OPENCLAW.hasName)
            desc = g.value(ev, OPENCLAW.hasDescription)
            name_str = str(name).lower() if name else ""
            desc_str = str(desc).lower() if desc else ""
            if not any(kw.lower() in name_str or kw.lower() in desc_str for kw in keywords):
                continue

        details = format_event(ev, g, show_agents=show_agents)
        results.append(details)

    # Sort by time
    results.sort(key=lambda x: x.get("time", ""))

    return results


def print_events(results: list, verbose: bool = False):
    """Print events in a human-readable format."""
    if not results:
        print("No events found.")
        return

    for i, ev in enumerate(results, 1):
        time_str = ev.get("time", "unknown time")
        name_str = ev.get("name", "unnamed event")
        evtype_str = ev.get("type", "")
        desc_str = ev.get("description", "")

        print(f"{i}. {name_str}")
        if time_str:
            print(f"   🕐 {time_str}")
        if evtype_str:
            print(f"   📋 Type: {evtype_str}")
        if desc_str:
            print(f"   📝 {desc_str}")
        if "location" in ev:
            print(f"   📍 {ev['location']}")
        if "agents" in ev and ev["agents"]:
            print(f"   👤 {', '.join(ev['agents'])}")
        if "source" in ev:
            print(f"   📄 {ev['source']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Query events from partitioned event graph files.")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--person", dest="person_uri", help="Person URI (e.g. kg:person-bill)")
    parser.add_argument("--event-type", dest="event_type", choices=["travel", "meeting", "social", "task", "system", "daily"])
    parser.add_argument("--keywords", nargs="+", help="Keywords to search in event name/description")
    parser.add_argument("--show-agents", action="store_true", help="Show agents/participants")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    results = query_events(
        from_date=args.from_date,
        to_date=args.to_date,
        person_uri=args.person_uri,
        event_type=args.event_type,
        keywords=args.keywords,
        show_agents=args.show_agents,
        verbose=args.verbose,
    )

    print_events(results, verbose=args.verbose)


if __name__ == "__main__":
    main()
