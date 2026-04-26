#!/usr/bin/env python3
"""
add_concept.py — Add a new Class or Property to the OpenClaw Core Ontology.

Appends the new concept as Turtle triples to core.ttl, then updates CHANGELOG.md.
Always run validate.py afterwards to ensure the ontology remains consistent.

Usage:
    # Add a Class
    python add_concept.py \\
        --type Class \\
        --name Task \\
        --description "A unit of work tracked within the OpenClaw system." \\
        --superclass openclaw:Concept

    # Add a DatatypeProperty
    python add_concept.py \\
        --type DatatypeProperty \\
        --name hasDeadline \\
        --description "The deadline datetime for this Task." \\
        --domain openclaw:Task \\
        --range xsd:dateTime \\
        --required

    # Add an ObjectProperty
    python add_concept.py \\
        --type ObjectProperty \\
        --name assignedTo \\
        --description "The Agent responsible for this Task." \\
        --domain openclaw:Task \\
        --range openclaw:Agent

Options:
    --type            Class | DatatypeProperty | ObjectProperty  [required]
    --name            Local name, e.g. Task or hasDeadline       [required]
    --description     Natural-language description                [required]
    --superclass      For Class: rdfs:subClassOf (e.g. openclaw:Concept)
    --domain          For Property: rdfs:domain
    --range           For Property: rdfs:range
    --required        Add SHACL sh:minCount 1 constraint (properties only)
    --ontology FILE   Path to core.ttl (default: ../ontology/core.ttl)
    --shapes FILE     Path to shapes.ttl (default: ../ontology/shapes.ttl)
    --changelog FILE  Path to CHANGELOG.md (default: ../ontology/CHANGELOG.md)
    --dry-run         Print what would be written without modifying files
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ONTOLOGY_DIR = SCRIPT_DIR.parent / "ontology"

OPENCLAW_NS = "urn:openclaw:ontology#"
PREFIX_MAP = {
    "openclaw:": OPENCLAW_NS,
    "owl:": "http://www.w3.org/2002/07/owl#",
    "rdfs:": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd:": "http://www.w3.org/2001/XMLSchema#",
    "rdf:": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


def expand_curie(curie: str) -> str:
    for prefix, ns in PREFIX_MAP.items():
        if curie.startswith(prefix):
            return f"<{ns}{curie[len(prefix):]}>"
    if curie.startswith("http") or curie.startswith("urn"):
        return f"<{curie}>"
    return curie  # return as-is if unknown


def build_class_turtle(name: str, description: str, superclass: str | None) -> str:
    lines = [
        f"openclaw:{name}",
        f"    a owl:Class ;",
        f"    rdfs:label   \"{name}\" ;",
    ]
    if superclass:
        lines.append(f"    rdfs:subClassOf {superclass} ;")
    # Escape description for Turtle
    desc_escaped = description.replace('"', '\\"')
    lines.append(f"    rdfs:comment \"\"\"{desc_escaped}\"\"\" .")
    return "\n".join(lines)


def build_property_turtle(
    name: str,
    prop_type: str,
    description: str,
    domain: str | None,
    range_: str | None,
) -> str:
    owl_type = f"owl:{prop_type}"
    lines = [
        f"openclaw:{name}",
        f"    a {owl_type} ;",
        f"    rdfs:label   \"{name}\" ;",
    ]
    if domain:
        lines.append(f"    rdfs:domain  {domain} ;")
    if range_:
        lines.append(f"    rdfs:range   {range_} ;")
    desc_escaped = description.replace('"', '\\"')
    lines.append(f"    rdfs:comment \"{desc_escaped}\" .")
    return "\n".join(lines)


def build_shacl_turtle(
    name: str,
    domain: str,
    range_: str | None,
    required: bool,
    existing_shape_name: str | None,
) -> str | None:
    """Build a SHACL property constraint block for insertion into shapes.ttl."""
    if not domain:
        return None
    # Derive the shape name: openclaw:XShape where X is the domain local name
    domain_local = domain.replace("openclaw:", "")
    shape_name = f"openclaw:{domain_local}Shape"
    prop_block = [
        f"    sh:property [",
        f"        sh:path        openclaw:{name} ;",
    ]
    if range_ and "xsd:" in range_:
        prop_block.append(f"        sh:datatype    {range_} ;")
    elif range_:
        prop_block.append(f"        sh:class       {range_} ;")
    if required:
        prop_block.append(f"        sh:minCount    1 ;")
        prop_block.append(f"        sh:message     \"'{name}' is required.\" ;")
    prop_block.append(f"    ] ;")
    return f"# Append inside {shape_name} in shapes.ttl:\n" + "\n".join(prop_block)


def append_to_ontology(path: Path, turtle_block: str, dry_run: bool) -> None:
    separator = "\n\n###############################################################################\n"
    new_content = separator + "# Added by add_concept.py\n###############################################################################\n\n" + turtle_block + "\n"
    if dry_run:
        print(f"\n--- Would append to {path} ---")
        print(new_content)
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅  Appended to {path}")


def update_changelog(path: Path, name: str, concept_type: str, description: str, dry_run: bool) -> None:
    today = date.today().isoformat()
    entry = (
        f"\n## [Unreleased] — {today}\n\n"
        f"### Added\n\n"
        f"- `openclaw:{name}` ({concept_type}): {description}\n"
    )
    if dry_run:
        print(f"\n--- Would prepend to {path} ---")
        print(entry)
        return

    existing = path.read_text(encoding="utf-8")
    # Insert after the first H1 heading
    match = re.search(r"^# .+$", existing, re.MULTILINE)
    if match:
        insert_pos = match.end()
        new_content = existing[:insert_pos] + "\n" + entry + existing[insert_pos:]
    else:
        new_content = entry + existing
    path.write_text(new_content, encoding="utf-8")
    print(f"✅  Updated {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a new Class or Property to the OpenClaw Core Ontology."
    )
    parser.add_argument(
        "--type",
        dest="concept_type",
        choices=["Class", "DatatypeProperty", "ObjectProperty"],
        required=True,
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--superclass", default=None, help="For Class: rdfs:subClassOf value.")
    parser.add_argument("--domain", default=None, help="For Property: rdfs:domain (e.g. openclaw:Task).")
    parser.add_argument("--range", dest="range_", default=None, help="For Property: rdfs:range.")
    parser.add_argument("--required", action="store_true", help="Add sh:minCount 1 SHACL constraint.")
    parser.add_argument("--ontology", type=Path, default=ONTOLOGY_DIR / "core.ttl")
    parser.add_argument("--shapes", type=Path, default=ONTOLOGY_DIR / "shapes.ttl")
    parser.add_argument("--changelog", type=Path, default=ONTOLOGY_DIR / "CHANGELOG.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Validate name format
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", args.name):
        print("ERROR: --name must be a valid identifier (letters, digits, underscores).", file=sys.stderr)
        sys.exit(1)

    # Check file existence
    for f in (args.ontology, args.shapes, args.changelog):
        if not f.exists():
            print(f"ERROR: File not found: {f}", file=sys.stderr)
            sys.exit(2)

    # Build Turtle block
    if args.concept_type == "Class":
        block = build_class_turtle(args.name, args.description, args.superclass)
    else:
        block = build_property_turtle(
            args.name, args.concept_type, args.description, args.domain, args.range_
        )

    print(f"\nConcept to add:\n{'-'*40}\n{block}\n{'-'*40}")

    if not args.dry_run:
        confirm = input("\nProceed? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    # Write to ontology
    append_to_ontology(args.ontology, block, args.dry_run)

    # Print SHACL hint if applicable
    if args.concept_type in ("DatatypeProperty", "ObjectProperty"):
        shacl_hint = build_shacl_turtle(
            args.name, args.domain or "", args.range_, args.required, None
        )
        if shacl_hint:
            print(f"\n📋  SHACL constraint to add to shapes.ttl:\n{shacl_hint}")

    # Update changelog
    update_changelog(args.changelog, args.name, args.concept_type, args.description, args.dry_run)

    print(
        "\n⚠️  Remember to:\n"
        "  1. Bump the version in core.ttl (owl:versionInfo)\n"
        "  2. Run: python scripts/validate.py\n"
        "  3. Update the version in ontology/CHANGELOG.md\n"
    )


if __name__ == "__main__":
    main()
