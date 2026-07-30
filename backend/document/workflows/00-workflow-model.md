# Workflow model reference

Shared shape for workflow documents in MongoDB, REST schemas, and runtime (`RuntimeWorkflow`).

REST: [01-create-workflow-diagrams.md](./01-create-workflow-diagrams.md) · runtime at chat: [../chat/04-workflow-runtime-at-chat-diagrams.md](../chat/04-workflow-runtime-at-chat-diagrams.md)

**Runtime:** [workflow_graph_compiler.py](../../app/domain/workflow/workflow_graph_compiler.py) + [workflow_graph_runner.py](../../app/domain/workflow/workflow_graph_runner.py) compile `nodes` + `edges` to LangGraph `StateGraph`. Mongo schema and REST **unchanged**.

---

## Document fields

| Field | Type | Notes |
|-------|------|--------|
| `id` | string | Mongo `_id` |
| `name` | string | Used for `workflow_<name>` delegate tool at chat |
| `description` | string \| null | Builder UI |
| `agent_id` | string \| null | Parent agent when attached |
| `routing_hint` | string \| null | Phase A — synced to `agent.capability_catalog.workflows` |
| `status` | `draft` \| `published` | Only **published** workflows load into `RuntimeBundle` |
| `nodes` | array | Canvas nodes (see below) |
| `edges` | array | Directed edges between nodes |
| `organization_id` | string | Org scope |

Schemas: [workflow.py](../../app/schemas/workflow.py) · runtime: [runtime_bundle.py](../../app/domain/models/runtime_bundle.py) (`RuntimeWorkflow`)

---

## Node shape

Each node in `nodes[]`:

| Field | Type | Notes |
|-------|------|--------|
| `id` | string | Unique within workflow |
| `type` | string | Runtime handler — [workflow_graph_compiler.py](../../app/domain/workflow/workflow_graph_compiler.py) |
| `position` | object | Canvas `{ x, y }` — not used at runtime |
| `data` | object | Type-specific payload |

### Supported `type` values (runtime)

| `type` | `data` keys (common) | Behavior |
|--------|----------------------|----------|
| `start` | — | Entry; runner follows first outgoing edge |
| `message` | `text`, `buttons?` | Emit assistant text; `{{slot}}` substitution |
| `input` | `slot_name` or label, `prompt`, `validation`, `retry_message` | Capture user message into named slot |
| `output` | `text` or `label` | User-facing reply |
| `end` | `text?` | Optional farewell; clears `active_flow_state` |

Edges: `{ "id", "source", "target" }` — runner uses `source` → `target` only.

---

## Session state (`tracker.active_flow_state`)

Set when a workflow enters; cleared on `end` or exit.

| Key | Purpose |
|-----|---------|
| `workflow_id` | Active `RuntimeWorkflow.id` |
| `current_node_id` | Node being executed |
| `slots` | `dict` of captured slot values |
| `awaiting_slot` | Slot name when waiting for user input on an `input` node |

Runner: [workflow_graph_runner.py](../../app/domain/workflow/workflow_graph_runner.py) · outer routing: [chat_graph.py](../../app/domain/graph/chat_graph.py) · [migration-langchain-proper.md](../agentic/updets/migration-langchain-proper.md) (**Done**)
