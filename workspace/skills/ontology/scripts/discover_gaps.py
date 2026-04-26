#!/usr/bin/env python3
"""
discover_gaps.py — Find KG content not covered by the OpenClaw ontology.

Loads a Knowledge Graph (TriG or Turtle) and the core ontology, then reports:
  1. Classes used in the KG that are NOT defined in the ontology
  2. Properties used in the KG that are NOT defined in the ontology

Output is a prioritized checklist that the user can review before invoking
add_concept.py to formally add any confirmed gaps.

Usage:
    python discover_gaps.py --kg path/to/graph.trig
    python discover_gaps.py --kg path/to/graph.trig --ontology ../ontology/core.ttl
    python discover_gaps.py --kg path/to/graph.trig --output gaps.md

Options:
    --kg FILE        Path to the Knowledge Graph file (.ttl or .trig) [required]
    --ontology FILE  Path to core.ttl (default: ../ontology/core.ttl)
    --output FILE    Write Markdown gap report to file (default: stdout)
    --ignore FILE    Path to a text file listing URIs to ignore (one per line)
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from rdflib import ConjunctiveGraph, Graph, Namespace, RDF, OWL
except ImportError:
    print("ERROR: Install rdflib with: pip install rdflib", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = Path(__file__).parent
ONTOLOGY_DIR = SCRIPT_DIR.parent / "ontology"

OPENCLAW = Namespace("urn:openclaw:ontology#")
OPENCLAW_KG = "urn:openclaw:kg:"

# Namespaces to skip (built-in RDF/OWL/RDFS/XSD terms are not "gaps")
BUILTIN_PREFIXES = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2002/07/owl#",
    "http://www.w3.org/2001/XMLSchema#",
    "http://www.w3.org/ns/shacl#",
    "http://purl.org/dc/terms/",
)


def curie(uri: str) -> str:
    replacements = {
        "urn:openclaw:ontology#": "openclaw:",
        "urn:openclaw:kg:": "kg:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    }
    for long, short in replacements.items():
        if uri.startswith(long):
            return short + uri[len(long):]
    return uri


def is_builtin(uri: str) -> bool:
    return any(uri.startswith(p) for p in BUILTIN_PREFIXES)


def load_ignored(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


def load_ontology_vocab(ont_path: Path) -> tuple[set[str], set[str]]:
    """Load defined classes and properties from the ontology."""
    g = Graph()
    g.parse(str(ont_path), format="turtle")

    defined_classes = {
        str(s) for s in g.subjects(RDF.type, OWL.Class)
        if str(s).startswith("urn:openclaw:ontology#")
    }
    defined_props = set()
    for prop_type in (OWL.DatatypeProperty, OWL.ObjectProperty, OWL.AnnotationProperty):
        for s in g.subjects(RDF.type, prop_type):
            if str(s).startswith("urn:openclaw:ontology#"):
                defined_props.add(str(s))

    return defined_classes, defined_props


def load_kg_vocab(kg_path: Path) -> tuple[set[str], set[str], int]:
    """Extract all classes and properties used in the KG."""
    suffix = kg_path.suffix.lower()
    fmt = ".trig" if suffix == ".trig" else "turtle"
    g = ConjunctiveGraph() if fmt == ".trig" else Graph()
    g.parse(str(kg_path), format="trig" if fmt == ".trig" else "turtle")

    triple_count = len(g)

    used_classes: set[str] = set()
    used_props: set[str] = set()

    for s, p, o in g:
        ps = str(p)
        # Collect predicate as a used property
        if not is_builtin(ps):
            used_props.add(ps)
        # Collect rdf:type objects as used classes
        if ps == str(RDF.type):
            os = str(o)
            if not is_builtin(os):
                used_classes.add(os)

    return used_classes, used_props, triple_count


def generate_report(
    gaps_classes: set[str],
    gaps_props: set[str],
    kg_path: Path,
    ont_path: Path,
    triple_count: int,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Ontology Gap Report",
        "",
        f"**Generated:** {now}",
        f"**KG file:** `{kg_path}`",
        f"**Ontology:** `{ont_path}`",
        f"**KG triples scanned:** {triple_count}",
        "",
    ]

    if not gaps_classes and not gaps_props:
        lines += [
            "## ✅ No Gaps Found",
            "",
            "All classes and properties in the Knowledge Graph are covered by the ontology.",
        ]
        return "\n".join(lines)

    lines += [
        f"## Summary",
        "",
        f"- **Undefined classes:** {len(gaps_classes)}",
        f"- **Undefined properties:** {len(gaps_props)}",
        "",
        "> Review the items below and confirm which should be added to `core.ttl`.",
        "> Use `add_concept.py` to add confirmed gaps.",
        "",
    ]

    if gaps_classes:
        lines += ["## Undefined Classes", ""]
        for cls in sorted(gaps_classes):
            lines.append(f"- [ ] `{curie(cls)}` — _{cls}_")
        lines.append("")

    if gaps_props:
        lines += ["## Undefined Properties", ""]
        for prop in sorted(gaps_props):
            lines.append(f"- [ ] `{curie(prop)}` — _{prop}_")
        lines.append("")

    lines += [
        "## Next Steps",
        "",
        "For each confirmed gap, run:",
        "```bash",
        "python scripts/add_concept.py --type Class --name <Name> --description \"...\"",
        "# or",
        "python scripts/add_concept.py --type Property --name <name> --domain openclaw:X --range xsd:string --description \"...\"",
        "```",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover KG concepts not covered by the OpenClaw ontology."
    )
    parser.add_argument("--kg", type=Path, required=True, help="Path to the KG file.")
    parser.add_argument("--ontology", type=Path, default=ONTOLOGY_DIR / "core.ttl")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--ignore",
        type=Path,
        default=None,
        help="Text file with URIs to exclude from gap detection (one per line).",
    )
    args = parser.parse_args()

    if not args.kg.exists():
        print(f"ERROR: KG file not found: {args.kg}", file=sys.stderr)
        sys.exit(2)
    if not args.ontology.exists():
        print(f"ERROR: Ontology not found: {args.ontology}", file=sys.stderr)
        sys.exit(2)

    ignored = load_ignored(args.ignore)
    defined_classes, defined_props = load_ontology_vocab(args.ontology)
    used_classes, used_props, triple_count = load_kg_vocab(args.kg)

    gap_classes = (used_classes - defined_classes) - ignored
    gap_props = (used_props - defined_props) - ignored

    report = generate_report(gap_classes, gap_props, args.kg, args.ontology, triple_count)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Gap report written to {args.output}", file=sys.stderr)
    else:
        print(report)

    if gap_classes or gap_props:
        sys.exit(1)  # non-zero exit signals gaps were found
    sys.exit(0)


if __name__ == "__main__":
    main()
