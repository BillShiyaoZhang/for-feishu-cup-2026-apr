# Knowledge Graph Skill

The **Knowledge Graph Skill** manages the runtime data of your OpenClaw system. It powers the AI agent's ability to search through and interact with its own structural awareness.

While the *Ontology* skill defines the "rules of the universe" (what an agent is, what a skill is), the *Knowledge Graph* skill keeps track of the "actual universe" (the specific `Claw` Agent, the exactly installed skills like `weather` or `ontology`).

## Components

- **`kg/graph.trig`**: The primary database structured in the TriG format containing all named graphs (`agents`, `skills`, `tools`, `memories`, etc.).
- **`scripts/query_entity.py`**: A hybrid semantic and keyword search tool for agents to discover system capabilities effortlessly without needing raw SPARQL queries.
- **`scripts/manage_entity.py`**: A robust insertion and modification script that safeguards the data by performing automated backups to `kg/snapshots/` before writing changes.

## How it works

When a user asks: "Who can fetch my schedule?", the agent activates the `knowledge-graph` skill, invokes `query_entity.py` using `schedule` as context, and instantly finds the `microsoft-graph-calendar` skill.

When you install a new component, this skill allows the agent to permanently register it into the Triplestore so that its context is never lost.
