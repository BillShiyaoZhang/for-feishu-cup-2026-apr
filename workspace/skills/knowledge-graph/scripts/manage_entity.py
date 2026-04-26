#!/usr/bin/env python3
"""
manage_entity.py — Add, update, or remove entities in the Knowledge Graph.

Usage:
    # Agent
    python manage_entity.py --graph ../kg/graph.trig --type agent --id test-agent \\
        --name "Test Agent" --description "A test agent."

    # Person (FOAF)
    python manage_entity.py --graph ../kg/graph.trig --type person --id alice \\
        --name "Alice" --prop "foaf:givenName=Alice" --prop "openclaw:note=Works at Acme"

    # Location
    python manage_entity.py --graph ../kg/graph.trig --type location --id lab-e4002 \\
        --name "Lab E-4002" --description "Arduino kit storage."

    # Event (uses event:Event from C4DM ontology)
    python manage_entity.py --graph ../kg/graph-events-2026-Q2.trig --type event \\
        --id movie-night-apr10 --name "Movie Night" \\
        --description "Movie night at Cozy Coffee." \\
        --event-type social --event-time "2026-04-10T19:00:00+08:00" \\
        --agent kg:person-bill --source-file "~/.openclaw/workspace/skills/knowledge-graph/kg/graph-events-2026-Q2.trig"

    # Delete
    python manage_entity.py --graph ../kg/graph.trig --type agent --id my-agent --delete

    # Skip validation (rare, use with caution)
    python manage_entity.py --graph ../kg/graph.trig --type agent --id test --no-validate

NOTE: Entity IDs use HYPHENS, not slashes. kg:skill/my-skill is INVALID.
      Use kg:skill-my-skill instead.
"""
import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, OWL, XSD

SCRIPT_DIR = Path(__file__).parent.resolve()
ONTOLOGY_DIR = SCRIPT_DIR.parent.parent / "ontology"
DEFAULT_VALIDATE_SCRIPT = ONTOLOGY_DIR / "scripts" / "validate.py"


def backup_graph(graph_path: Path):
    snapshots_dir = graph_path.parent / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = snapshots_dir / f"{today}.trig"
    shutil.copy2(graph_path, backup_path)
    print(f"[manage_entity] Backed up {graph_path.name} → {backup_path.name}", file=sys.stderr)
    return backup_path


def run_validation(graph_path: Path, validate_script: Path) -> bool:
    """Run SHACL validation on the graph. Returns True if conforms."""
    venv_python = Path(sys.executable)
    if not validate_script.exists():
        print(f"[manage_entity] WARNING: validate script not found at {validate_script}", file=sys.stderr)
        return True

    try:
        result = subprocess.run(
            [str(venv_python), str(validate_script), "--data", str(graph_path.resolve())],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print(f"[manage_entity] ✅ Validation passed", file=sys.stderr)
            return True
        else:
            print(f"[manage_entity] ❌ Validation FAILED:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[manage_entity] ❌ Validation timed out", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[manage_entity] ⚠️  Validation error: {exc}", file=sys.stderr)
        return True


def utc_now() -> str:
    """Return current UTC time in the format used by the KG: +00:00 timezone."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# Type → (class_uri_name, graph_name, namespace_prefix, rdf_type_value)
# For events, graph_name is derived from the filename (e.g. events-2026-Q2)
TYPE_MAP = {
    "agent":    ("Agent",    "agents",    "openclaw", "openclaw:Agent"),
    "skill":    ("Skill",    "skills",    "openclaw", "openclaw:Skill"),
    "tool":     ("Tool",     "tools",     "openclaw", "openclaw:Tool"),
    "memory":   ("Memory",   "memory",    "openclaw", "openclaw:Memory"),
    "concept":  ("Concept",  "concepts",  "openclaw", "openclaw:Concept"),
    "location": ("Location", "locations", "openclaw", "openclaw:Location"),
    "person":   ("Person",   "people",   "foaf",     "foaf:Person"),
    "event":    ("Event",    "events",    "event",    "event:Event"),
}

# Namespaces used in parsing
NAMESPACES = {
    "openclaw": "urn:openclaw:ontology#",
    "kg":       "urn:openclaw:kg:",
    "foaf":     "http://xmlns.com/foaf/0.1/",
    "event":    "http://purl.org/NET/c4dm/event.owl#",
    "xsd":      "http://www.w3.org/2001/XMLSchema#",
}


def parse_val(val: str, namespaces: dict) -> URIRef | Literal:
    """Parse a value string into an RDF node.

    Prefixes: kg:, openclaw:, foaf:, event:
      "true"/"false" → xsd:boolean
      numeric         → xsd:integer or xsd:decimal
      other           → xsd:string literal
    """
    for prefix, ns in namespaces.items():
        if val.startswith(f"{prefix}:"):
            return URIRef(val.replace(f"{prefix}:", ns))

    if val.lower() == "true":
        return Literal(True, datatype=XSD.boolean)
    elif val.lower() == "false":
        return Literal(False, datatype=XSD.boolean)

    try:
        if "." in val:
            return Literal(float(val))
        return Literal(int(val))
    except ValueError:
        return Literal(val)


def infer_graph_name_from_path(graph_path: Path) -> str:
    """Infer named graph name from filename for event types.

    e.g. graph-events-2026-Q2.trig → events-2026-Q2
    """
    name = graph_path.stem  # "graph-events-2026-Q2"
    if name.startswith("graph-"):
        name = name[6:]  # "events-2026-Q2"
    return name


def main():
    parser = argparse.ArgumentParser(
        description="Add, update, or remove an entity in the Knowledge Graph."
    )
    parser.add_argument(
        "--graph", type=Path, required=True,
        help="Path to graph.trig or graph-events-YYYY-QN.trig"
    )
    parser.add_argument(
        "--type", required=True,
        choices=list(TYPE_MAP.keys()),
        help="Entity type"
    )
    parser.add_argument(
        "--id", required=True,
        help="Entity ID (slug, use hyphens not slashes)"
    )
    parser.add_argument("--name", help="Human-readable name")
    parser.add_argument("--description", help="Entity description")
    parser.add_argument(
        "--prop", action="append", default=[],
        help="Extra properties, e.g. 'openclaw:usesSkill=kg:skill-ontology'"
    )

    # Event-specific arguments
    parser.add_argument(
        "--event-type", choices=["travel", "meeting", "social", "task", "system", "daily"],
        help="Event type (openclaw:eventType)"
    )
    parser.add_argument(
        "--event-time", help="Event time (xsd:dateTime, e.g. 2026-04-10T19:00:00+08:00)"
    )
    parser.add_argument(
        "--agent", action="append", default=[],
        help="Agent/person (kg:person-xxx). Can be specified multiple times."
    )
    parser.add_argument(
        "--location", help="Location (kg:location-xxx or free text)"
    )
    parser.add_argument(
        "--source-file", help="Path to original memory file (openclaw:sourceFile)"
    )

    parser.add_argument(
        "--delete", action="store_true",
        help="Delete the entity instead of adding/updating"
    )
    parser.add_argument(
        "--no-validate", action="store_true",
        help="Skip SHACL validation after saving (rare, use with caution)"
    )
    parser.add_argument(
        "--validate-script", type=Path, default=DEFAULT_VALIDATE_SCRIPT,
        help=f"Path to validate.py (default: {DEFAULT_VALIDATE_SCRIPT})"
    )

    args = parser.parse_args()

    if not args.graph.exists():
        print(f"ERROR: Graph file not found: {args.graph}", file=sys.stderr)
        sys.exit(2)

    # ── Backup ────────────────────────────────────────────────────────────────
    backup_graph(args.graph)

    # ── Load graph ────────────────────────────────────────────────────────────
    g = ConjunctiveGraph()
    g.parse(str(args.graph), format="trig")

    # Build namespace objects
    NS = {k: Namespace(v) for k, v in NAMESPACES.items()}
    for prefix, ns in NS.items():
        g.bind(prefix, ns)

    OPENCLAW = NS["openclaw"]
    KG       = NS["kg"]
    FOAF     = NS["foaf"]
    EVENT    = NS["event"]

    # ── Resolve type ─────────────────────────────────────────────────────────
    class_name, base_graph_name, ns_prefix, _ = TYPE_MAP[args.type]

    if ns_prefix == "openclaw":
        class_uri = OPENCLAW[class_name]
    elif ns_prefix == "foaf":
        class_uri = FOAF[class_name]
    elif ns_prefix == "event":
        class_uri = EVENT["Event"]
    else:
        class_uri = OPENCLAW[class_name]

    entity_uri = KG[f"{args.type}-{args.id}"]

    # For events, infer named graph from filename
    if args.type == "event":
        graph_name = infer_graph_name_from_path(args.graph)
    else:
        graph_name = base_graph_name

    named_graph_uri = URIRef(f"urn:openclaw:graph:{graph_name}")
    context = g.get_context(named_graph_uri)

    # ── Delete path ───────────────────────────────────────────────────────────
    if args.delete:
        context.remove((entity_uri, None, None))
        g.serialize(destination=str(args.graph), format="trig")
        print(f"[manage_entity] Deleted {entity_uri}", file=sys.stderr)
        sys.exit(0)

    # ── Add / Update path ────────────────────────────────────────────────────
    context.add((entity_uri, RDF.type, class_uri))

    if args.name:
        if args.type == "person":
            context.set((entity_uri, FOAF.name, Literal(args.name)))
        else:
            context.set((entity_uri, OPENCLAW.hasName, Literal(args.name)))

    if args.description:
        context.set((entity_uri, OPENCLAW.hasDescription, Literal(args.description)))

    # ── Event-specific fields ─────────────────────────────────────────────────
    if args.type == "event":
        if args.event_type:
            context.add((entity_uri, OPENCLAW.eventType, Literal(args.event_type)))

        if args.event_time:
            context.add((entity_uri, EVENT.time, Literal(args.event_time, datatype=XSD.dateTime)))

        for agent_uri in args.agent:
            agent_node = parse_val(agent_uri, NS)
            context.add((entity_uri, EVENT.agent, agent_node))

        if args.location:
            loc_node = parse_val(args.location, NS)
            context.add((entity_uri, OPENCLAW.eventLocation, loc_node))

        if args.source_file:
            context.add((entity_uri, OPENCLAW.sourceFile, Literal(args.source_file)))

    # ── Generic properties ────────────────────────────────────────────────────
    for p in args.prop:
        if "=" not in p:
            continue
        k, v = p.split("=", 1)

        # Resolve property prefix
        prop_ns = k.split(":")[0] if ":" in k else "openclaw"
        if prop_ns in NS:
            prop_uri = NS[prop_ns][k.split(":", 1)[1]]
        else:
            prop_uri = OPENCLAW[k]

        val_node = parse_val(v, NS)
        context.add((entity_uri, prop_uri, val_node))

    # ── Timestamps ────────────────────────────────────────────────────────────
    now_str = utc_now()
    context.set((entity_uri, OPENCLAW.updatedAt, Literal(now_str, datatype=XSD.dateTime)))
    if not list(context.objects(entity_uri, OPENCLAW.createdAt)):
        context.add((entity_uri, OPENCLAW.createdAt, Literal(now_str, datatype=XSD.dateTime)))

    # ── Serialize ─────────────────────────────────────────────────────────────
    g.serialize(destination=str(args.graph), format="trig")
    print(f"[manage_entity] Saved {entity_uri} ({args.type})", file=sys.stderr)

    # ── Validate ─────────────────────────────────────────────────────────────
    if not args.no_validate:
        ok = run_validation(args.graph.resolve(), args.validate_script.resolve())
        if not ok:
            print("[manage_entity] ❌ Validation failed — graph NOT validated.", file=sys.stderr)
            print("[manage_entity] Run with --no-validate to override, or fix the entity data.", file=sys.stderr)
            sys.exit(1)
    else:
        print("[manage_entity] ⚠️  Validation skipped (--no-validate)", file=sys.stderr)

    print(f"[manage_entity] ✅ Done", file=sys.stderr)


if __name__ == "__main__":
    main()
