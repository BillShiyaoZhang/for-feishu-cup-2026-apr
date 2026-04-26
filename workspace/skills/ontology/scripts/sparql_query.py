#!/usr/bin/env python3
"""
sparql_query.py — Run SPARQL queries against the ontology or a KG file.

Usage:
    python sparql_query.py --graph ../ontology/core.ttl --query "SELECT ?s WHERE { ?s a owl:Class }"
    python sparql_query.py --graph ../examples/skill_example.ttl --file ../examples/sample_queries.sparql
    python sparql_query.py --graph ../kg/graph.trig --file my_query.sparql --format table

Options:
    --graph FILE    Path to a .ttl or .trig graph to query (required)
    --query TEXT    Inline SPARQL query string
    --file FILE     Path to a .sparql file containing the query
    --format        Output format: table (default) | csv | json
    --limit N       Limit results to N rows (default: 100)

Exactly one of --query or --file must be provided.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

try:
    from rdflib import ConjunctiveGraph, Graph
    from rdflib.plugins.sparql import prepareQuery
except ImportError:
    print(
        "ERROR: Missing dependency. Install with:\n  pip install rdflib",
        file=sys.stderr,
    )
    sys.exit(2)

COMMON_PREFIXES = """
PREFIX owl:      <http://www.w3.org/2002/07/owl#>
PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:      <http://www.w3.org/2001/XMLSchema#>
PREFIX sh:       <http://www.w3.org/ns/shacl#>
PREFIX openclaw: <urn:openclaw:ontology#>
PREFIX kg:       <urn:openclaw:kg:>
"""


def load_graph(path: Path) -> Graph:
    suffix = path.suffix.lower()
    fmt = {".ttl": "turtle", ".trig": "trig", ".n3": "n3", ".nt": "nt"}.get(
        suffix, "turtle"
    )
    g = ConjunctiveGraph() if fmt == "trig" else Graph()
    try:
        g.parse(str(path), format=fmt)
    except Exception as exc:
        print(f"ERROR: Cannot parse {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    return g


def shorten(uri: str) -> str:
    """Replace known namespace URIs with readable prefixes."""
    replacements = {
        "http://www.w3.org/2002/07/owl#": "owl:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/2001/XMLSchema#": "xsd:",
        "http://www.w3.org/ns/shacl#": "sh:",
        "urn:openclaw:ontology#": "openclaw:",
        "urn:openclaw:kg:": "kg:",
    }
    for long, short in replacements.items():
        if uri.startswith(long):
            return short + uri[len(long):]
    return uri


def format_value(val) -> str:
    if val is None:
        return ""
    s = str(val)
    return shorten(s)


def print_table(vars_: list, rows: list) -> None:
    if not rows:
        print("(no results)")
        return
    # Compute column widths
    col_widths = [len(v) for v in vars_]
    str_rows = []
    for row in rows:
        str_row = [format_value(row.get(v)) for v in vars_]
        str_rows.append(str_row)
        for i, cell in enumerate(str_row):
            col_widths[i] = max(col_widths[i], len(cell))

    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header = "| " + " | ".join(v.ljust(col_widths[i]) for i, v in enumerate(vars_)) + " |"
    print(sep)
    print(header)
    print(sep)
    for sr in str_rows:
        print("| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(sr)) + " |")
    print(sep)
    print(f"\n{len(rows)} result(s).")


def print_csv(vars_: list, rows: list) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(vars_)
    for row in rows:
        writer.writerow([format_value(row.get(v)) for v in vars_])


def print_json(vars_: list, rows: list) -> None:
    out = []
    for row in rows:
        out.append({v: format_value(row.get(v)) for v in vars_})
    print(json.dumps(out, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a SPARQL query against an RDF graph."
    )
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--file", type=Path, default=None)
    parser.add_argument("--format", choices=["table", "csv", "json"], default="table")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if not args.query and not args.file:
        parser.error("Provide either --query TEXT or --file PATH.")
    if args.query and args.file:
        parser.error("Provide only one of --query or --file, not both.")

    if not args.graph.exists():
        print(f"ERROR: Graph file not found: {args.graph}", file=sys.stderr)
        sys.exit(2)

    # Load graph
    g = load_graph(args.graph)
    print(f"Loaded {len(g)} triples from {args.graph.name}\n", file=sys.stderr)

    # Load query
    if args.file:
        query_text = args.file.read_text(encoding="utf-8")
    else:
        query_text = args.query

    full_query = COMMON_PREFIXES + "\n" + query_text

    # Execute
    try:
        results = g.query(full_query)
    except Exception as exc:
        print(f"ERROR: SPARQL execution failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if results.type == "CONSTRUCT" or results.type == "DESCRIBE":
        # For CONSTRUCT/DESCRIBE, serialize as Turtle
        result_graph = results.graph
        print(result_graph.serialize(format="turtle"))
        return

    if results.type == "ASK":
        answer = "true" if bool(results) else "false"
        print(f"ASK result: {answer}")
        return

    # SELECT results
    vars_ = [str(v) for v in results.vars]
    rows = list(results)[:args.limit]

    if args.format == "table":
        print_table(vars_, rows)
    elif args.format == "csv":
        print_csv(vars_, rows)
    elif args.format == "json":
        print_json(vars_, rows)


if __name__ == "__main__":
    main()
