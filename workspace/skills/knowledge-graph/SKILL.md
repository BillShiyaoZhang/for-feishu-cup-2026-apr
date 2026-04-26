---
name: knowledge-graph
description: >
  Manage and query factual data instances in the OpenClaw Knowledge Graph.
  Activate when you need to query entities or when the user wants to add/update
  a new agent, skill, tool, person, location, concept, or event in the system.
---

# Knowledge Graph (KG) Skill

This skill governs the OpenClaw instance Knowledge Graph. While the `ontology` skill defines the system *schema*, this skill maintains the *data*—the actual capabilities, agents, people, locations, concepts, and episodic events in your workspace.

### KG File Structure

| File | Content | Loading |
|---|---|---|
| `graph.trig` | Core KG: agents, skills, people, locations, concepts | Always |
| `graph-events-YYYY-QN.trig` | Event KG: episodic/event memories by quarter | On-demand |

### KG Instances vs. Skill Files

KG data (e.g., `kg:skill-spawn-agent`) is distinct from the real skill on disk
(`<workspace>/skills/spawn-agent/SKILL.md`). KG instances are *records* of those
files; they do not replace them.

### ⚠️ Turtle Prefixed Name Constraint

**Local part (after `:`) cannot contain `/`.** Use hyphens instead.

| ✅ Correct | ❌ Wrong |
|---|---|
| `kg:skill-agent-registry` | `kg:skill/agent-registry` |
| `kg:agent-business-manager` | `kg:agent/business-manager` |

## When to Use

- **Resource Discovery**: Find agents, skills, tools, people, or locations matching a description.
- **Entity Management**: Create, update, or delete agents/skills/people/locations/concepts.
- **Event Logging**: Record time-lined events (travel, meetings, social, tasks, system events).
- **Event Query**: Query events by time range, person, or type.

## 1. Querying Entities (Core KG)

```bash
python3 skills/knowledge-graph/scripts/query_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --query "keyword or feature description"
```

## 2. Querying Events (Event KG)

```bash
# Query events by time range
python3 skills/knowledge-graph/scripts/query_events.py \
  --from 2026-04-01 --to 2026-04-30

# Query events for a specific person
python3 skills/knowledge-graph/scripts/query_events.py \
  --person kg:person-bill --from 2026-03-01 --to 2026-04-30

# Query events by type
python3 skills/knowledge-graph/scripts/query_events.py \
  --event-type travel --from 2026-01-01 --to 2026-12-31

# Show agents/participants
python3 skills/knowledge-graph/scripts/query_events.py \
  --from 2026-04-01 --to 2026-04-30 --show-agents
```

## 2b. Natural Language Query — query_natural.py

For natural language questions about Bill, use `query_natural.py`:

```bash
~/.openclaw/venvs/kg/bin/python3 \
  ~/.openclaw/workspace/skills/knowledge-graph/scripts/query_natural.py \
  "Bill 4月份见过哪些人"
```

**This is the primary interface for Bill's memory queries.** It returns:
- `schema_context`: ground-truth ontology schema (event types, property names, enum values) — **prevents LLM hallucination**
- `parsed_params`: structured query parameters
- `ontology_snippet`: raw ontology excerpt for reference

The agent uses `schema_context` to construct valid KG queries without making up field names or enum values.

## 2c. Legacy Query — query_about.py

For structured questions about Bill ("Bill 的行程" / "Bill 认识谁"), `query_about.py` still works as a rule-based fallback:

```bash
~/.openclaw/venvs/kg/bin/python3 \
  ~/.openclaw/workspace/skills/knowledge-graph/scripts/query_about.py "Bill"

# 行程模式（按时间排序）
~/.openclaw/venvs/kg/bin/python3 \
  ~/.openclaw/workspace/skills/knowledge-graph/scripts/query_about.py "Bill 的行程"

# 人物模式（从事件中发现相关人员）
~/.openclaw/venvs/kg/bin/python3 \
  ~/.openclaw/workspace/skills/knowledge-graph/scripts/query_about.py "Bill 认识谁"
```

Supported modes:
- `all` (default) — entities + events, sorted by relevance score
- `travel` — only travel events, sorted by time (newest first)
- `people` — person entities + related people from events
- `location` — location entities only

**Internal use:** Call via `exec` tool using the KG runtime Python (`~/.openclaw/venvs/kg/bin/python3`). Parse stdout as structured text output.

## 3. Managing Entities

Use `manage_entity.py` to add/update/delete entities. It auto-backs up and runs SHACL validation.

**Example: Add a Person**
```bash
python3 skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type person --id alice \
  --name "Alice" \
  --prop "foaf:givenName=Alice" \
  --prop "openclaw:note=Works at Acme Corp"
```

**Example: Add a Location**
```bash
python3 skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type location --id lab-e4002 \
  --name "Lab E-4002" \
  --description "Arduino kit storage lab."
```

**Example: Add an Agent**
```bash
python3 skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type agent --id my-agent \
  --name "My Agent" \
  --description "A test agent." \
  --prop "openclaw:agentId=my-agent" \
  --prop "openclaw:isDefaultAgent=false"
```

**Delete an Entity**
```bash
python3 skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph.trig \
  --type agent --id my-agent --delete
```

## 4. Managing Events

Events are stored in partitioned `graph-events-YYYY-QN.trig` files. Determine the correct quarter from the event date, then write to the corresponding file.

**Example: Add an Event**
```bash
python3 skills/knowledge-graph/scripts/manage_entity.py \
  --graph skills/knowledge-graph/kg/graph-events-2026-Q2.trig \
  --type event \
  --id movie-night-apr24 \
  --name "AFCT Dome Immersive Cinema" \
  --description "AFCT Dome Immersive Cinema screening at XEC Campus G1015." \
  --event-type social \
  --event-time "2026-04-24T14:00:00+08:00" \
  --agent kg:person-bill \
  --source-file "~/.openclaw/workspace/skills/knowledge-graph/kg/graph-events-2026-Q2.trig"
```

### Event Types

| Type | Use for |
|---|---|
| `travel` | Trains, flights, transportation |
| `meeting` | Meetings, discussions, collaborations |
| `social` | Social activities, events, gatherings |
| `task` | Tasks, work, coursework |
| `system` | System events, architecture changes, config updates |
| `daily` | General daily records |

### Event Fields

| Field | Property | Notes |
|---|---|---|
| Name | `openclaw:hasName` | `--name` |
| Description | `openclaw:hasDescription` | `--description` |
| Event type | `openclaw:eventType` | `--event-type` |
| Time | `event:time` | `--event-time` (xsd:dateTime) |
| Agents | `event:agent` | `--agent` (can repeat) |
| Location | `openclaw:eventLocation` | `--location` (kg: or free text) |
| Source file | `openclaw:sourceFile` | `--source-file` (original log) |

## Supported Types

| Type | Class | Graph File |
|---|---|---|
| `agent` | `openclaw:Agent` | `graph.trig` |
| `skill` | `openclaw:Skill` | `graph.trig` |
| `tool` | `openclaw:Tool` | `graph.trig` |
| `concept` | `openclaw:Concept` | `graph.trig` |
| `location` | `openclaw:Location` | `graph.trig` |
| `person` | `foaf:Person` | `graph.trig` |
| `event` | `event:Event` | `graph-events-YYYY-QN.trig` |

## Property Prefix Reference

| Prefix | Namespace | Use for |
|--------|-----------|---------|
| `kg:` | `urn:openclaw:kg:` | References to KG entities |
| `openclaw:` | `urn:openclaw:ontology#` | OpenClaw properties |
| `foaf:` | `http://xmlns.com/foaf/0.1/` | FOAF properties (for `person`) |
| `event:` | `http://purl.org/NET/c4dm/event.owl#` | Event ontology (for `event`) |

## Required Fields (SHACL Constraints)

| Type | Required Fields |
|---|---|
| Agent | `openclaw:agentId` (via `--prop`) |
| Skill | `openclaw:hasTriggerCondition` (via `--prop`) |
| Event | `openclaw:eventType` + `event:time` |

> `manage_entity.py` sets `RDF.type` and timestamps (`createdAt`/`updatedAt`) automatically.

## ⚠️ Execution Environment — Read Before Calling

**KG scripts require rdflib — use the workspace venv Python, NOT system Python.**

| Script | Runtime Entity | Python Path |
|---|---|---|
| `manage_entity.py` | `kg:concept-runtime-kg` | `/home/shiyao/.openclaw/venvs/kg/bin/python3` |
| `query_events.py` | `kg:concept-runtime-kg` | `/home/shiyao/.openclaw/venvs/kg/bin/python3` |
| `query_entity.py` | `kg:concept-runtime-kg` | `/home/shiyao/.openclaw/venvs/kg/bin/python3` |
| `query_about.py` | `kg:concept-runtime-kg` | `/home/shiyao/.openclaw/venvs/kg/bin/python3` |
| `sync.py` (kg-sync) | `kg:concept-runtime-kg` | `/home/shiyao/.openclaw/venvs/kg/bin/python3` |
| `graph_calendar.py` | `kg:concept-runtime-calendar` | `/home/shiyao/.openclaw/venvs/calendar/bin/python3` |

**KG Runtime entities (in `graph.trig`):**
- `kg:concept-runtime-kg` — KG venv (`~/.openclaw/venvs/kg/`, rdflib, pyshacl)
- `kg:concept-runtime-calendar` — Calendar Python (stdlib, Graph API)
- `kg:concept-runtime-node` — Node.js v22
- `kg:concept-runtime-mcp` — MiniMax MCP env (`/tmp/mcp-env/`)

Each skill's `requiresRuntime` property in KG links to its runtime entity.

**Rule: ALL python calls use uv-managed venvs.** Never use system `/usr/bin/python3`. Even stdlib-only scripts must use a uv-managed venv. This keeps all python execution under uv management.

**Calling pattern:**
```bash
# ✅ Correct — uv-managed venv python
/home/shiyao/.openclaw/venvs/kg/bin/python3 ~/.openclaw/workspace/skills/knowledge-graph/scripts/manage_entity.py --graph ...

# ❌ Wrong — system python not managed by uv
python3 ~/.openclaw/workspace/skills/knowledge-graph/scripts/manage_entity.py --graph ...
```
