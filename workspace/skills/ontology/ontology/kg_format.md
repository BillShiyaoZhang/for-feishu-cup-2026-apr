# Knowledge Graph Format Specification

**Version:** 0.1.0
**Ontology:** [OpenClaw Core Ontology](./core.ttl) v0.1.0
**Status:** Draft

> This document defines the canonical storage format for the OpenClaw Knowledge Graph (KG).
> It is intended as a reference for the future **KG skill** that will implement read/write
> operations on the graph. The ontology skill reads but does not write to the KG.

---

## Format Choice: RDF TriG

The KG is stored as **[RDF TriG](https://www.w3.org/TR/trig/)** (`.trig`), a superset of Turtle
that adds support for **Named Graphs**.

### Why TriG?

| Requirement | How TriG satisfies it |
|-------------|----------------------|
| Schema compatibility | Same prefix/namespace convention as `core.ttl` (Turtle) |
| SPARQL compatibility | Natively supported by rdflib and all major triple stores |
| Partitioning | Named graphs segment data by domain (skills, agents, memories…) |
| Provenance | Named graph URI encodes the domain; metadata can be attached to each graph |
| Tooling | rdflib, Apache Jena, GraphDB, Stardog all support TriG natively |

---

## File Layout

```
kg/
├── graph.trig              # Primary KG — all named graphs combined
└── snapshots/
    └── YYYY-MM-DD.trig     # Daily snapshots for rollback
```

The `graph.trig` file is the **single source of truth**. Snapshots are read-only archives.

---

## Named Graph Convention

Each domain of entities lives in its own named graph:

| Named Graph URI | Contents |
|----------------|----------|
| `urn:openclaw:graph:skills` | All `openclaw:Skill` instances |
| `urn:openclaw:graph:agents` | All `openclaw:Agent` instances |
| `urn:openclaw:graph:tools` | All `openclaw:Tool` instances |
| `urn:openclaw:graph:memories` | All `openclaw:Memory` instances |
| `urn:openclaw:graph:concepts` | All `openclaw:Concept` subclass instances |
| `urn:openclaw:graph:meta` | Graph-level metadata (versions, timestamps) |

---

## Instance URI Convention

```
urn:openclaw:kg:{type}/{id}
```

| Segment | Rule |
|---------|------|
| `type` | Lowercase class name (e.g. `skill`, `agent`, `tool`, `memory`, `concept`) |
| `id` | Slug: lowercase, hyphens replacing spaces (e.g. `run-command`, `antigravity`) |

**Examples:**
```
urn:openclaw:kg:skill/ontology
urn:openclaw:kg:agent/antigravity
urn:openclaw:kg:tool/run-command
urn:openclaw:kg:memory/user-pref-dark-mode
```

---

## TriG File Structure

A well-formed `graph.trig` file:

```turtle
# Namespace declarations (shared across all graphs)
@prefix owl:       <http://www.w3.org/2002/07/owl#> .
@prefix rdf:       <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:      <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:       <http://www.w3.org/2001/XMLSchema#> .
@prefix openclaw:  <urn:openclaw:ontology#> .
@prefix kg:        <urn:openclaw:kg:> .

# ── Graph: Meta ───────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:meta> {
    <urn:openclaw:graph:meta>
        dcterms:created  "2026-04-01T00:00:00Z"^^xsd:dateTime ;
        dcterms:modified "2026-04-01T00:00:00Z"^^xsd:dateTime ;
        owl:versionInfo  "0.1.0" .
}

# ── Graph: Skills ─────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:skills> {
    kg:skill/ontology
        a openclaw:Skill ;
        openclaw:hasName          "ontology" ;
        openclaw:hasDescription   "Manages the OpenClaw Core Ontology." ;
        openclaw:createdAt        "2026-04-01T00:00:00Z"^^xsd:dateTime .
}

# ── Graph: Agents ─────────────────────────────────────────────────────────────
GRAPH <urn:openclaw:graph:agents> {
    kg:agent/antigravity
        a openclaw:Agent ;
        openclaw:hasName          "Antigravity" ;
        openclaw:hasDescription   "The primary OpenClaw AI coding assistant." ;
        openclaw:createdAt        "2026-01-01T00:00:00Z"^^xsd:dateTime .
}
```

---

## Validation

All instances in `graph.trig` must conform to the SHACL shapes in `ontology/shapes.ttl`.

Run validation with:
```bash
python skills/ontology/scripts/validate.py --data kg/graph.trig
```

Expected output for a valid graph:
```
✅  Ontology / data graph validates successfully.
```

---

## SPARQL Queries on the KG

The KG supports the full **SPARQL 1.1** query language via rdflib.

```bash
# List all Skills
python skills/ontology/scripts/sparql_query.py \
  --graph kg/graph.trig \
  --query "SELECT ?name WHERE { ?s a openclaw:Skill ; openclaw:hasName ?name }"
```

See `examples/sample_queries.sparql` for 10 ready-to-use query templates.

---

## Snapshot Strategy

The KG skill (future) should create a snapshot before any destructive operation:

```bash
cp kg/graph.trig kg/snapshots/$(date +%Y-%m-%d).trig
```

Snapshots are kept for 30 days by default (cleanup policy TBD by KG skill).

---

## Relationship to the Ontology

```
core.ttl          → defines what classes/properties CAN exist (schema)
shapes.ttl        → enforces what MUST be present (constraints)
graph.trig        → the actual data (instances)
```

The ontology skill manages `core.ttl` and `shapes.ttl`.
The KG skill (future) manages `graph.trig`.
