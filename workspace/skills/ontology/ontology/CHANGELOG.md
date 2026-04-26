# OpenClaw Ontology — CHANGELOG

All notable changes to `core.ttl` and `shapes.ttl` are documented here.
Format follows [Semantic Versioning](https://semver.org/).

---

## [0.3.0] — 2026-04-02

### Strategy Change

This release adopts a **"best vocabulary" composition strategy**: instead of
reinventing established concepts under the `openclaw:` namespace, the ontology
now directly imports and reuses six standard vocabularies as building blocks.
The `openclaw:` namespace is now reserved exclusively for (a) system-layer
concepts, (b) bridge properties connecting the system to world-knowledge
entities, and (c) OpenClaw-specific extensions with no standard equivalent.

### Added — New External Vocabulary Prefixes

Six vocabularies are now declared as building-block namespaces in `core.ttl`
and `shapes.ttl`:

| Prefix | Namespace | Purpose |
|--------|-----------|---------|
| `foaf:` | `http://xmlns.com/foaf/0.1/` | Person, social relationships |
| `vcard:` | `http://www.w3.org/2006/vcard/ns#` | Contact info, addresses |
| `org:` | `http://www.w3.org/ns/org#` | Organizations, membership, roles |
| `event:` | `http://purl.org/NET/c4dm/event.owl#` | Events (agent/place/time) |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | Topics, concept hierarchies |
| `time:` | `http://www.w3.org/2006/time#` | Time intervals and instants |

### Added — Agent ↔ Person Bridge Properties

New `openclaw:` properties connecting the system layer to `foaf:Person`:

- `openclaw:knownAs` — `Agent → foaf:Person` — the agent knows this person
- `openclaw:sendsMessageTo` — `Channel → foaf:Person` — peer-to-person mapping
- `openclaw:preferredPeer` — `foaf:Person → xsd:string` — preferred peer id string (format: `<channelType>:<peerId>`)
- `openclaw:language` — `foaf:Person → xsd:string` — BCP 47 language tag(s)
- `openclaw:note` — `foaf:Person → xsd:string` — free-text annotation
- `openclaw:jobTitle` — `foaf:Person → xsd:string` — professional title label

### Added — Event Extension Properties

New `openclaw:` properties extending `event:Event` instances:

- `openclaw:eventLabel` — `event:Event → xsd:string` — human-readable event name
- `openclaw:eventNote` — `event:Event → xsd:string` — free-text observation/outcome
- `openclaw:sourceMemory` — `event:Event → openclaw:Memory` — provenance link to source memory
- `openclaw:relatedTopic` — `event:Event → skos:Concept` — topic(s) discussed at the event

### Added — Memory Link Properties

New `openclaw:` properties linking `openclaw:Memory` to world-knowledge entities:

- `openclaw:aboutPerson` — `Memory → foaf:Person` — memory is about this person
- `openclaw:aboutEvent` — `Memory → event:Event` — memory is about this event
- `openclaw:aboutTopic` — `Memory → skos:Concept` — memory relates to this topic

### Updated — Existing Properties

- `openclaw:relatedTo` — domain/range widened from `openclaw:Concept` to `owl:Thing`,
  enabling cross-type associations (e.g., `foaf:Person ← relatedTo → event:Event`).
- `openclaw:Concept.rdfs:comment` — updated to reflect its new role as an extension
  placeholder for concepts not covered by external standard vocabularies.

### Added — SHACL Shapes

New shapes in `shapes.ttl`:

- `openclaw:PersonExtShape` — validates`openclaw:` extension properties on `foaf:Person` nodes
  (targetSubjectsOf `openclaw:preferredPeer`)
- `openclaw:EventExtShape` — validates `openclaw:` extension properties on `event:Event` nodes
  (targetSubjectsOf `openclaw:eventLabel`)

Updated shapes:

- `AgentShape` — added `openclaw:knownAs → foaf:Person` constraint
- `ChannelShape` — added `openclaw:sendsMessageTo → foaf:Person` constraint
- `MemoryShape` — added `aboutPerson`, `aboutEvent`, `aboutTopic` optional property constraints
- `ConceptShape` — `relatedTo` constraint relaxed from `sh:class openclaw:Concept` to `sh:nodeKind sh:BlankNodeOrIRI`

### Added — Examples

- `examples/person_event_example.ttl` — a multi-vocabulary KG sample demonstrating
  `foaf:Person` + `org:Organization` + `event:Event` + `skos:Concept` + `openclaw:Memory` used together.

### Vocabulary Decision Notes

- **Schema.org** rejected: designed for SEO/search-engine display, not memory reasoning.
- **PIMO** rejected as direct dependency: design philosophy adopted, but vocabulary
  is unmaintained (NEPOMUK/NRL ecosystem); FOAF+ORG+Event provide equivalent expressiveness.
- **NCO** rejected: unmaintained; W3C vCard Ontology covers the contact info domain.
- **NIE** deferred to a future release (requires OS-level file/email indexing).

---

## [0.2.0] — 2026-04-01

### Breaking Changes (MAJOR bump)

- `openclaw:Memory` semantics corrected: no longer a generic storage unit.
  Now specifically represents Markdown-file-based memory as per the OpenClaw
  docs. Properties `memoryType` enum values changed from
  `fact|preference|interaction|summary|derived` → `longterm|daily|derived`.
- Removed: `openclaw:invokedBy` (Skill → Agent) — superseded by `openclaw:usesSkill`.
- Removed: `openclaw:hasSkillPath` path convention changed (now points to
  skill root directory, not SKILL.md file directly).

### Added (MINOR)

**New Classes:**
- `openclaw:Gateway` — the central daemon process (WebSocket server, channel manager)
- `openclaw:Node` — client device connecting to Gateway with role=node
- `openclaw:Provider` — LLM service integration (OpenAI, Anthropic, Gemini, Ollama, etc.)
- `openclaw:Workspace` — Agent's filesystem home directory with bootstrap files
- `openclaw:Channel` — messaging platform integration (WhatsApp, Telegram, Discord, etc.)
- `openclaw:Session` — conversation instance with message history and routing state
- `openclaw:Binding` — routing rule mapping inbound messages to an Agent
- `openclaw:Plugin` — packaged extension adding tools, skills, or channels

**New Properties:**
- Global: `openclaw:docUrl` (xsd:anyURI)
- Gateway: `openclaw:bindHost`, `openclaw:managesChannel`, `openclaw:hostsAgent`, `openclaw:connectedNode`
- Agent: `openclaw:agentId`, `openclaw:hasWorkspace`, `openclaw:usesProvider`, `openclaw:hasSession`, `openclaw:usesSkill`, `openclaw:isDefaultAgent`
- Skill: `openclaw:skillPrecedence`, `openclaw:isUserInvocable`, `openclaw:disableModelInvocation`, `openclaw:targetPlatform`
- Tool: `openclaw:toolGroup`, `openclaw:isBuiltin`, `openclaw:providedByPlugin`
- Channel: `openclaw:channelType`, `openclaw:accountId`, `openclaw:isPlugin`
- Session: `openclaw:sessionId`, `openclaw:dmScope`, `openclaw:sessionTranscriptPath`
- Binding: `openclaw:routesToAgent`, `openclaw:matchesChannel`, `openclaw:matchesPeerId`
- Memory: `openclaw:memoryFilePath`, `openclaw:memoryBackend`
- Provider: `openclaw:providerName`, `openclaw:modelRef`, `openclaw:isLocalProvider`

**New SHACL Shapes:**
- `openclaw:GatewayShape`, `openclaw:WorkspaceShape`, `openclaw:ChannelShape`,
  `openclaw:SessionShape`, `openclaw:BindingShape`, `openclaw:ProviderShape`,
  `openclaw:PluginShape`, `openclaw:DocUrlShape`

**Updated SHACL Shapes:**
- `AgentShape` — added agentId (required), hasWorkspace, usesProvider, usesSkill, isDefaultAgent
- `SkillShape` — added hasTriggerCondition (now required), skillPrecedence (1-6 enum),
  isUserInvocable, disableModelInvocation, targetPlatform
- `ToolShape` — added toolGroup (group:* enum), isBuiltin, providedByPlugin
- `MemoryShape` — updated memoryType enum; added memoryBackend (builtin|qmd|honcho)
- `ChannelShape` — channelType enum covers all 23 supported channels

### Documentation Sources
- https://docs.openclaw.ai/concepts/architecture (Gateway, Node)
- https://docs.openclaw.ai/concepts/agent (Agent, Workspace, Skills, Tools)
- https://docs.openclaw.ai/concepts/agent-workspace (Workspace file map)
- https://docs.openclaw.ai/concepts/memory (Memory backends and types)
- https://docs.openclaw.ai/concepts/session (Session scopes and lifecycle)
- https://docs.openclaw.ai/concepts/multi-agent (Agent, Binding, routing rules)
- https://docs.openclaw.ai/channels (Channel types)
- https://docs.openclaw.ai/tools (Tool groups)
- https://docs.openclaw.ai/tools/skills (Skill frontmatter, loading order)
- https://docs.openclaw.ai/providers (Provider list)

---

## [0.1.0] — 2026-04-01

### Added (Initial Release)

**Classes:**
- `openclaw:Skill` — functional module with trigger condition and instructions
- `openclaw:Memory` — persistent information unit
- `openclaw:Tool` — invocable capability (e.g. run_command, browser)
- `openclaw:Agent` — intelligent entity that executes tasks
- `openclaw:Concept` — generic extension node for domain-specific types

**Datatype Properties:**
- `openclaw:hasName`, `openclaw:hasDescription`, `openclaw:version`,
  `openclaw:createdAt`, `openclaw:updatedAt`, `openclaw:hasTriggerCondition`,
  `openclaw:hasSkillPath`, `openclaw:memoryContent`, `openclaw:memoryType`,
  `openclaw:dependsOn`, `openclaw:invokedBy`, `openclaw:usesTool`,
  `openclaw:hasMemory`, `openclaw:relatedTo`
