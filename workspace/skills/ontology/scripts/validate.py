#!/usr/bin/env python3
"""
validate.py — SHACL validation for the OpenClaw Core Ontology.

Usage:
    python validate.py                          # validate core.ttl itself
    python validate.py --data path/to/kg.trig   # validate a Knowledge Graph

Options:
    --data FILE     Path to a .ttl or .trig KG data file to validate.
                    If omitted, validates the ontology's own example files.
    --ontology FILE Path to core.ttl (default: ../ontology/core.ttl)
    --shapes FILE   Path to shapes.ttl (default: ../ontology/shapes.ttl)
    --inference     Enable RDFS inference before validation (default: rdfs)
    --verbose       Print full SHACL report even when valid

Exit codes:
    0 — all shapes conform
    1 — validation failures found
    2 — file not found or parse error
"""
import argparse
import sys
from pathlib import Path

try:
    from rdflib import Graph, ConjunctiveGraph
    from pyshacl import validate
except ImportError:
    print(
        "ERROR: Missing dependencies. Install them with:\n"
        "  pip install rdflib pyshacl",
        file=sys.stderr,
    )
    sys.exit(2)

SCRIPT_DIR = Path(__file__).parent
ONTOLOGY_DIR = SCRIPT_DIR.parent / "ontology"
EXAMPLES_DIR = SCRIPT_DIR.parent / "examples"


def load_graph(path: Path) -> Graph:
    """Load a Turtle or TriG file into an rdflib Graph."""
    suffix = path.suffix.lower()
    fmt_map = {".ttl": "turtle", ".trig": "trig", ".n3": "n3", ".nt": "nt"}
    fmt = fmt_map.get(suffix, "turtle")
    g = ConjunctiveGraph() if fmt == "trig" else Graph()
    try:
        g.parse(str(path), format=fmt)
    except Exception as exc:
        print(f"ERROR: Could not parse {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    return g


def run_validation(
    data_graph: Graph,
    shapes_path: Path,
    ontology_path: Path,
    inference: str = "rdfs",
    verbose: bool = False,
) -> bool:
    """Run SHACL validation. Returns True if conforms."""
    shapes_graph = load_graph(shapes_path)
    ont_graph = load_graph(ontology_path)

    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference=inference,
        abort_on_first=False,
        debug=False,
    )

    if conforms:
        print("✅  Ontology / data graph validates successfully.")
        if verbose:
            print("\n--- SHACL Report ---")
            print(report_text)
    else:
        print("❌  Validation FAILED. Violations found:\n")
        print(report_text)

    return conforms


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run SHACL validation on the OpenClaw ontology or a KG file."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="Path to the KG data file (.ttl or .trig) to validate.",
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=ONTOLOGY_DIR / "core.ttl",
        help="Path to core.ttl (default: ontology/core.ttl).",
    )
    parser.add_argument(
        "--shapes",
        type=Path,
        default=ONTOLOGY_DIR / "shapes.ttl",
        help="Path to shapes.ttl (default: ontology/shapes.ttl).",
    )
    parser.add_argument(
        "--inference",
        choices=["none", "rdfs", "owlrl", "both"],
        default="rdfs",
        help="Inference mode (default: rdfs).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full SHACL report even when validation passes.",
    )
    args = parser.parse_args()

    # Resolve data graph: use provided file or fall back to all examples
    if args.data:
        data_path = args.data.resolve()
        if not data_path.exists():
            print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
            sys.exit(2)
        print(f"Validating: {data_path}")
        data_graph = load_graph(data_path)
    else:
        # Validate all example files bundled with the skill
        print(f"No --data provided. Validating example files in {EXAMPLES_DIR}...")
        data_graph = Graph()
        for example in sorted(EXAMPLES_DIR.glob("*.ttl")):
            print(f"  Loading: {example.name}")
            data_graph += load_graph(example)

    ok = run_validation(
        data_graph,
        shapes_path=args.shapes,
        ontology_path=args.ontology,
        inference=args.inference,
        verbose=args.verbose,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
