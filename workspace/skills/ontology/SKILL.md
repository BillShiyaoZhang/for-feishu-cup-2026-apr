---
name: ontology
description: >
  Activate this skill when the user wants to view, manage, extend, or validate
  the OpenClaw system ontology. Also activate when gaps are found between the
  Knowledge Graph and the ontology definition, or when new concepts need to be
  formally added to the system blueprint. Also activate when the user wants to
  add or update knowledge about people, organizations, events, or topics —
  these world-knowledge concepts are now part of the ontology as external
  vocabulary building blocks (foaf:, org:, event:, skos:).

  Keywords: ontology, knowledge graph, concept, class, property, SHACL,
  validate, gap, add concept, OWL, RDF, SPARQL, blueprint, schema,
  person, contact, organization, company, team, event, meeting, topic,
  subject, FOAF, vCard, vocabulary, prefix, foaf, org, skos.
---

# Ontology Skill

This skill manages the **OpenClaw Core Ontology** — the structured blueprint
that defines all concepts, relationships, and constraints in the OpenClaw
system. The ontology is stored as **OWL 2 / Turtle** (`ontology/core.ttl`)
and validated with **SHACL** (`ontology/shapes.ttl`).

**Key boundary:** This skill owns the *schema* (`core.ttl`, `shapes.ttl`).
It does NOT own the Knowledge Graph data (`graph.trig`). The KG is managed
by a separate KG skill. Never write `graph.trig` from this
skill — only read it for gap analysis.

---

## File Layout

```
skills/ontology/
├── SKILL.md                     ← agent instructions (this file)
├── README.md                    ← human-readable guide and best practices
├── ontology/
│   ├── core.ttl                 ← OWL 2 ontology (source of truth)
│   ├── shapes.ttl               ← SHACL validation constraints
│   ├── kg_format.md             ← KG storage format specification (RDF TriG)
│   └── CHANGELOG.md             ← version history
├── scripts/
│   ├── validate.py              ← run SHACL validation
│   ├── nl_export.py             ← export ontology as natural language
│   ├── sparql_query.py          ← run SPARQL queries
│   ├── discover_gaps.py         ← find KG content not covered by ontology
│   └── add_concept.py           ← add a new class or property to ontology
├── templates/
│   └── concept_summary.j2       ← Jinja2 template for NL export
├── examples/
│   ├── skill_example.ttl        ← sample KG instance: a Skill
│   ├── agent_example.ttl        ← sample KG instance: full system config
│   └── sample_queries.sparql    ← 10 ready-to-use SPARQL queries
└── docs/
    └── ontology_overview.md     ← detailed concept reference
```

---

## Behaviors

### 1. View Current Ontology

When the user asks to see what concepts are defined:

```
python skills/ontology/scripts/nl_export.py
```

This renders `core.ttl` into a readable Markdown summary. Present the output
to the user directly.

### 2. Validate Ontology

When the user asks to validate or check consistency:

```
python skills/ontology/scripts/validate.py
```

Runs pySHACL against `core.ttl` using `shapes.ttl`. Report:
- ✅ "Ontology validates successfully." if it conforms.
- ❌ List each violation with the affected node, path, and constraint message.

**Always run this after any modification to `core.ttl` or `shapes.ttl`.**

### 3. Discover Gaps

When the user wants to find concepts in the KG not yet covered by the ontology:

```
python skills/ontology/scripts/discover_gaps.py --kg <path-to-kg.trig>
```

Present the output as a prioritised checklist. Treat output as a backlog:
- **High priority:** Unknown classes (structural gaps — need a new class)
- **Low priority:** Unknown properties on known classes (annotation gaps)

Do NOT immediately add every gap. Present the list to the user and ask which
items they want to formalise. An entity that appeared only once may not deserve
a permanent class.

### 4. Add a New Concept

When the user confirms a gap or explicitly requests adding a concept:

1. Ask the user for all required info:
   - **Type**: Class or Property?
   - **Name**: (e.g. `Task`, `hasDeadline`)
   - **Description**: natural-language definition
   - **Domain / Range** (for properties)
   - **Required?** (i.e., add SHACL `sh:minCount 1` constraint)
2. Show the user a **draft** of the new Turtle snippet before writing.
3. If approved, run:
   ```
   python skills/ontology/scripts/add_concept.py \
     --type Class \
     --name Task \
     --description "A unit of work tracked within the OpenClaw system." \
     --superclass openclaw:Concept
   ```
4. Bump version in `core.ttl` (`owl:versionInfo`) — new class = MINOR bump.
5. Run `validate.py` to confirm the file is still valid.
6. Update `ontology/CHANGELOG.md` with what was added.
7. If adding a new class, also add a corresponding `NodeShape` in `shapes.ttl`
   (minimum: enforce `hasName` and `hasDescription` as required).

### 5. Run a SPARQL Query (System Introspection)

You (the Agent) should **proactively** translate the user's natural language questions into SPARQL queries to interrogate the Knowledge Graph (`graph.trig`). Use this capability for:

- **Troubleshooting / Debugging:** e.g. "Why isn't the Work agent replying on WhatsApp?" (Query bindings, channels, and agent links to find disconnected components).
- **Impact Analysis:** e.g. "What happens if I delete this Discord channel?" (Query which agents rely on the channel via bindings).
- **Security Audits:** e.g. "Which agents have access to file system tools?" (Query `Agent → usesTool → Tool(group:fs)`).
- **Meta-Questions:** e.g. "List all my tools that are not built-in."

```bash
python skills/ontology/scripts/sparql_query.py \
  --graph <path-to-trig-or-ttl> \
  --query "<SPARQL string or path to .sparql file>"
```

**Instructions for you (the Agent):**
1. Do not expect the user to write SPARQL. **YOU** must write the query based on their natural language request.
2. Refer to `examples/sample_queries.sparql` for the correct core ontology prefixes, syntax, and common patterns.
3. Execute the script and return the results to the user as a clean, formatted Markdown table or a conversational summary.
4. **Boundary:** SPARQL is for **exploration, reporting, and auditing** only. Never use it as a live fast-path data source for your own real-time routing decisions.

### 6. Export Ontology Summary

When the user wants a sharable document:

```
python skills/ontology/scripts/nl_export.py --output docs/ontology_overview.md
```

---

## Versioning Rules

The ontology follows **Semantic Versioning** (tracked in `owl:versionInfo`
in `core.ttl`):

| Change Type | Version Bump |
|---|---|
| Remove or rename a class/property | **MAJOR** (x.0.0) |
| Add a new class or property | **MINOR** (0.x.0) |
| Fix description, comment, tighten a constraint | **PATCH** (0.0.x) |

**Always update `ontology/CHANGELOG.md` when changing `core.ttl`.** If the
changelog is not updated, the audit trail is broken.

---

## Decision Rules

These rules govern how this skill should behave when making decisions:

### Schema before data
`core.ttl` is the single source of truth. New KG instances must only use
classes and properties already defined in `core.ttl`. The correct flow is:

> New idea → Add to `core.ttl` first → Update `CHANGELOG.md` → Then populate KG

Never create KG data for an undefined concept and backfill the schema later.

### Keep `shapes.ttl` in sync with `core.ttl`
Every new class added to `core.ttl` must have a corresponding `NodeShape`
in `shapes.ttl`. The minimum viable shape enforces `hasName` (required) and
`hasDescription` (required). Any property with a closed set of valid values
(e.g. `channelType`, `memoryType`, `dmScope`) must use `sh:in` to enumerate them.

### Do not over-model
Only add a concept when it is confirmed as a stable, reusable idea.
Resist the urge to pre-define every possible concept. Use `openclaw:Concept`
as a placeholder for fuzzy ideas, and promote them to proper classes only when
their properties and relationships are understood.

### Use `add_concept.py` for additions — not manual edits
The script ensures consistent Turtle format, correct prefix usage, and
auto-updates the CHANGELOG. Manual edits to `core.ttl` are valid but higher
risk; if done manually, always validate immediately after.

---

## Constraints & Guardrails

- **Never** remove or rename a class/property without explicit user confirmation.
- **Always** run `validate.py` after any modification to `core.ttl` or `shapes.ttl`.
- **Never** write to `core.ttl` without also updating `ontology/CHANGELOG.md`.
- **Always** show a draft to the user before writing new Turtle to `core.ttl`.
- **Never** write to `graph.trig` from this skill — that is the KG skill's scope.
- When in doubt about a new concept, present it as a draft and ask the user.
