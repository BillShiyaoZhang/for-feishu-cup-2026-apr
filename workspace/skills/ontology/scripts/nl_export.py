#!/usr/bin/env python3
"""
nl_export.py — Export the OpenClaw ontology as human-readable natural language.

Reads core.ttl and renders every class and property into a Markdown document
using a Jinja2 template. The output is suitable for LLM consumption or for
sharing with users who are unfamiliar with RDF/OWL syntax.

Usage:
    python nl_export.py                      # print to stdout
    python nl_export.py --output FILE        # write to file

Options:
    --ontology FILE   Path to core.ttl (default: ../ontology/core.ttl)
    --shapes FILE     Path to shapes.ttl (default: ../ontology/shapes.ttl)
    --template FILE   Path to Jinja2 template (default: ../templates/concept_summary.j2)
    --output FILE     Write output to file (default: stdout)
"""
import argparse
import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print(
        "ERROR: Missing dependencies. Install with:\n"
        "  pip install rdflib jinja2",
        file=sys.stderr,
    )
    sys.exit(2)

SCRIPT_DIR = Path(__file__).parent
ONTOLOGY_DIR = SCRIPT_DIR.parent / "ontology"
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"

OPENCLAW = Namespace("urn:openclaw:ontology#")
SH = Namespace("http://www.w3.org/ns/shacl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")


def str_val(g: Graph, subject, predicate) -> str:
    """Return the first string value for (subject, predicate) or ''."""
    val = g.value(subject, predicate)
    return str(val) if val else ""


def curie(uri: str) -> str:
    """Convert a full URI to a readable CURIE."""
    replacements = {
        "urn:openclaw:ontology#": "openclaw:",
        "http://www.w3.org/2002/07/owl#": "owl:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2001/XMLSchema#": "xsd:",
    }
    for long, short in replacements.items():
        if uri.startswith(long):
            return short + uri[len(long):]
    return uri


def collect_classes(g: Graph) -> list[dict]:
    """Extract all OWL classes from the graph."""
    classes = []
    for cls in g.subjects(RDF.type, OWL.Class):
        if str(cls).startswith("urn:openclaw:ontology#"):
            classes.append(
                {
                    "uri": str(cls),
                    "curie": curie(str(cls)),
                    "label": str_val(g, cls, RDFS.label),
                    "comment": str_val(g, cls, RDFS.comment),
                }
            )
    return sorted(classes, key=lambda c: c["label"])


def collect_properties(g: Graph, cls_uri: str) -> list[dict]:
    """Extract all properties whose rdfs:domain matches cls_uri."""
    props = []
    for prop in g.subjects(RDFS.domain, g.store.__class__):
        pass  # placeholder — replaced below
    # Use a SPARQL query for precision
    q = f"""
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?prop ?label ?comment ?range ?kind WHERE {{
        ?prop rdf:type ?kind .
        ?prop rdfs:domain <{cls_uri}> .
        OPTIONAL {{ ?prop rdfs:label ?label }}
        OPTIONAL {{ ?prop rdfs:comment ?comment }}
        OPTIONAL {{ ?prop rdfs:range ?range }}
        FILTER (?kind IN (owl:DatatypeProperty, owl:ObjectProperty))
    }}
    ORDER BY ?label
    """
    for row in g.query(q):
        props.append(
            {
                "uri": str(row.prop),
                "curie": curie(str(row.prop)),
                "label": str(row.label) if row.label else curie(str(row.prop)),
                "comment": str(row.comment) if row.comment else "",
                "range": curie(str(row.range)) if row.range else "",
                "kind": "Datatype" if "Datatype" in str(row.kind) else "Object",
            }
        )
    return props


def collect_global_properties(g: Graph) -> list[dict]:
    """Properties with domain owl:Thing (apply to all classes)."""
    q = """
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?prop ?label ?comment ?range ?kind WHERE {
        ?prop rdf:type ?kind .
        ?prop rdfs:domain owl:Thing .
        OPTIONAL { ?prop rdfs:label ?label }
        OPTIONAL { ?prop rdfs:comment ?comment }
        OPTIONAL { ?prop rdfs:range ?range }
        FILTER (?kind IN (owl:DatatypeProperty, owl:ObjectProperty))
    }
    ORDER BY ?label
    """
    props = []
    for row in g.query(q):
        props.append(
            {
                "uri": str(row.prop),
                "curie": curie(str(row.prop)),
                "label": str(row.label) if row.label else curie(str(row.prop)),
                "comment": str(row.comment) if row.comment else "",
                "range": curie(str(row.range)) if row.range else "",
                "kind": "Datatype" if "Datatype" in str(row.kind) else "Object",
            }
        )
    return props


def collect_shacl_constraints(sg: Graph, cls_curie: str) -> list[dict]:
    """Extract SHACL constraints for a given class from the shapes graph."""
    cls_uri = cls_curie.replace("openclaw:", "urn:openclaw:ontology#")
    q = f"""
    PREFIX sh:   <http://www.w3.org/ns/shacl#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?path ?minCount ?maxCount ?datatype ?in_ ?message WHERE {{
        ?shape sh:targetClass <{cls_uri}> ;
               sh:property ?prop_node .
        ?prop_node sh:path ?path .
        OPTIONAL {{ ?prop_node sh:minCount ?minCount }}
        OPTIONAL {{ ?prop_node sh:maxCount ?maxCount }}
        OPTIONAL {{ ?prop_node sh:datatype ?datatype }}
        OPTIONAL {{ ?prop_node sh:message ?message }}
    }}
    ORDER BY ?path
    """
    constraints = []
    for row in sg.query(q):
        constraints.append(
            {
                "path": curie(str(row.path)),
                "minCount": str(row.minCount) if row.minCount else None,
                "maxCount": str(row.maxCount) if row.maxCount else None,
                "datatype": curie(str(row.datatype)) if row.datatype else None,
                "message": str(row.message) if row.message else None,
            }
        )
    return constraints


def build_context(g: Graph, sg: Graph) -> dict:
    """Build the full template rendering context."""
    classes = collect_classes(g)
    global_props = collect_global_properties(g)

    # Enrich each class
    for cls in classes:
        cls["properties"] = collect_properties(g, cls["uri"])
        cls["shacl"] = collect_shacl_constraints(sg, cls["curie"])

    # Ontology metadata
    ont_uri = "urn:openclaw:ontology"
    q_meta = f"""
    PREFIX owl:     <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT ?version ?label ?comment ?created WHERE {{
        <{ont_uri}> owl:versionInfo ?version ;
                    rdfs:label ?label ;
                    rdfs:comment ?comment .
        OPTIONAL {{ <{ont_uri}> dcterms:created ?created }}
    }}
    """
    metadata = {"version": "unknown", "label": "OpenClaw Core Ontology",
                 "comment": "", "created": ""}
    for row in g.query(q_meta):
        metadata = {
            "version": str(row.version),
            "label": str(row.label),
            "comment": str(row.comment),
            "created": str(row.created) if row.created else "",
        }
        break

    return {"metadata": metadata, "classes": classes, "global_props": global_props}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export OpenClaw ontology as natural-language Markdown."
    )
    parser.add_argument("--ontology", type=Path, default=ONTOLOGY_DIR / "core.ttl")
    parser.add_argument("--shapes", type=Path, default=ONTOLOGY_DIR / "shapes.ttl")
    parser.add_argument("--template", type=Path, default=TEMPLATES_DIR / "concept_summary.j2")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    for f in (args.ontology, args.shapes, args.template):
        if not f.exists():
            print(f"ERROR: File not found: {f}", file=sys.stderr)
            sys.exit(2)

    g = Graph()
    g.parse(str(args.ontology), format="turtle")

    sg = Graph()
    sg.parse(str(args.shapes), format="turtle")

    env = Environment(
        loader=FileSystemLoader(str(args.template.parent)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(args.template.name)
    ctx = build_context(g, sg)
    output = template.render(**ctx)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
