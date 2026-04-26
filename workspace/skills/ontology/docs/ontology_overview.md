# OpenClaw Ontology Skill — Overview

> **Skill version:** 0.1.0 | **Ontology version:** 0.1.0

The Ontology Skill gives OpenClaw a **structured, machine-verifiable blueprint** of its own
concepts. Instead of relying solely on natural language to define what a "Skill" or "Agent" is,
this skill maintains a formal **OWL 2 ontology** against which the Knowledge Graph is validated.

---

## Why an Ontology?

| Problem | Without ontology | With ontology |
|---------|-----------------|---------------|
| Concept drift | "Skill" means different things over time | One authoritative definition in `core.ttl` |
| Ambiguous relations | "agent uses tool" is vague | Formally typed: `openclaw:usesTool` is `ObjectProperty` |
| Data quality | KG can hold anything | SHACL enforces required fields and types |
| Discoverability | No way to know what's missing | `discover_gaps.py` flags undefined concepts |
| Explainability | AI must guess schema | `nl_export.py` renders schema as readable Markdown |

---

## What This Skill Provides

### 1. Core Ontology (`ontology/core.ttl`)

An **OWL 2** ontology defining 5 core classes:

| Class | Description |
|-------|-------------|
| `openclaw:Skill` | A functional module (SKILL.md-based) with a trigger condition |
| `openclaw:Agent` | An intelligent entity that invokes tools and skills |
| `openclaw:Tool` | An atomic capability (e.g. `run_command`, `browser`) |
| `openclaw:Memory` | A persistent information unit across conversations |
| `openclaw:Concept` | A generic extension node for domain-specific entities |

Global properties (apply to all classes): `hasName`, `hasDescription`, `version`,
`createdAt`, `updatedAt`.

### 2. Validation Shapes (`ontology/shapes.ttl`)

**SHACL** constraints that enforce data quality:
- Every Skill, Agent, Tool, Memory, Concept **must** have `hasName` (exactly 1) and `hasDescription` (≥1)
- `memoryType` must be one of: `fact | preference | interaction | summary | derived`
- All object property references are type-checked

### 3. Scripts

| Script | What it does |
|--------|-------------|
| `validate.py` | Runs SHACL validation; use after every ontology change |
| `nl_export.py` | Renders `core.ttl` as this readable Markdown document |
| `sparql_query.py` | Executes SPARQL 1.1 queries against any `.ttl` or `.trig` file |
| `discover_gaps.py` | Compares a KG file against the ontology; lists uncovered concepts |
| `add_concept.py` | Safely appends a new Class or Property to `core.ttl` with CHANGELOG update |

### 4. Knowledge Graph Format (`ontology/kg_format.md`)

Defines how the **future KG** should store data:
- Format: **RDF TriG** (`kg/graph.trig`)
- Named graphs per domain: `urn:openclaw:graph:skills`, `:agents`, `:tools`, etc.
- Instance URIs: `urn:openclaw:kg:{type}/{id}`

---

## Quick Start

```bash
# Install dependencies
pip install rdflib pyshacl jinja2

# Validate examples against core ontology
python skills/ontology/scripts/validate.py

# Export ontology as readable Markdown
python skills/ontology/scripts/nl_export.py

# List all defined OWL classes
python skills/ontology/scripts/sparql_query.py \
  --graph skills/ontology/ontology/core.ttl \
  --query "SELECT ?class ?label WHERE { ?class a owl:Class ; rdfs:label ?label }"

# Check for gaps between a KG and the ontology
python skills/ontology/scripts/discover_gaps.py --kg path/to/graph.trig

# Add a new concept (interactive)
python skills/ontology/scripts/add_concept.py \
  --type Class \
  --name Task \
  --description "A unit of work tracked in OpenClaw." \
  --superclass openclaw:Concept
```

---

## Versioning

The ontology follows **Semantic Versioning**:

| Change | Version bump |
|--------|-------------|
| Remove or rename class/property | **MAJOR** |
| Add new class or property | **MINOR** |
| Edit description, comment, constraint | **PATCH** |

All changes are logged in `ontology/CHANGELOG.md`.

---

## File Index

```
skills/ontology/
├── SKILL.md                         Agent entrypoint (trigger + instructions)
├── ontology/
│   ├── core.ttl                     OWL 2 ontology (source of truth)
│   ├── shapes.ttl                   SHACL validation shapes
│   ├── kg_format.md                 KG data format specification
│   └── CHANGELOG.md                 Version history
├── scripts/
│   ├── validate.py                  SHACL validation
│   ├── nl_export.py                 OWL → natural language
│   ├── sparql_query.py              SPARQL query tool
│   ├── discover_gaps.py             KG gap detection
│   └── add_concept.py               Add concepts interactively
├── templates/
│   └── concept_summary.j2           Jinja2 template for nl_export
├── examples/
│   ├── skill_example.ttl            Sample Skill KG instance
│   ├── agent_example.ttl            Sample Agent + Tools KG instances
│   └── sample_queries.sparql        10 ready-to-use SPARQL queries
└── docs/
    └── ontology_overview.md         This document
```
