# API migration — agentic system (capability catalog)

Single reference for **every REST endpoint** affected by the move to an agentic runtime:

- Final prompt layers: `[1] system_prompt` → `[2] guardrails` → `[3] capability_catalog` → `[4] rag_context` (Phase C only)
- `routing_hint` on attachable resources → stored in `agent.capability_catalog` (not in `system_prompt`)

**Related specs:**

- [../00-overview.md](../00-overview.md)
- [runtime-migration-agentic.md](./runtime-migration-agentic.md)

**Legend**

| Column | Meaning |
|--------|---------|
| **Route change** | New URL, method, or handler in `app/api/v1/*.py` |
| **Schema change** | Request/response Pydantic model in `app/schemas/*.py` |
| **Service change** | Logic in `app/services/*.py` or `agent_repository` |

---

## Summary

| Category | Count |
|----------|------:|
| Endpoints — **no change** | 22 |
| Endpoints — **schema/service only** (route unchanged) | 10 |
| **New** REST endpoints required (minimum migration) | **0** |
| **New** REST endpoints optional (builder UI) | 1 |

---

## Chat & preview (runtime)

Agentic behavior is **internal** (`FinalPromptBuilder` + catalog). Same URLs and `ChatRequest` / `ChatResponse`.

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/chat/webhook/{webhook_id}` | **No** | **No** | **No API work.** Runtime builds final prompt inside `ChatCompletionService`. Doc: [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) |
| `POST` | `/api/v1/agents/{agent_id}/preview/chat` | **No** | **No** | **No API work.** Same as webhook path with `for_preview=True`. Doc: [../../chat/06-preview-chat-diagrams.md](../../chat/06-preview-chat-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/preview/sessions/{sender_id}/trace` | **No** | **No** | **No API work.** Optional later: trace events for `capability_catalog_built`. Doc: [../../chat/07-preview-session-trace-diagrams.md](../../chat/07-preview-session-trace-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/runtime-graph` | **No** | **No** | **No API work.** Graph stays config topology. Doc: [../../chat/05-agent-runtime-graph-diagrams.md](../../chat/05-agent-runtime-graph-diagrams.md) |

**Route file:** `app/api/v1/chat.py`, `app/api/v1/agents.py` — **no edits required.**

---

## Agents

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `GET` | `/api/v1/agents` | **No** | **No** | **No API work.** Doc: [../../agent/03-list-agents-diagrams.md](../../agent/03-list-agents-diagrams.md) |
| `POST` | `/api/v1/agents` | **No** | **No** *(response)* | **Service only:** `agent_service.create_draft` must init Mongo field `capability_catalog` with empty sections `{ tools, knowledge_bases, workflows, sub_agents }`. Do **not** add catalog to `CreateAgentRequest`. Doc: [../../agent/01-create-agent-diagrams.md](../../agent/01-create-agent-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}` | **No** | **Optional Yes** | **Optional:** add `capability_catalog` to `GetAgentResponse` so builder UI can edit hints. Not required for Phase A if hints are set only via attach APIs. Doc: [../../agent/02-get-agent-diagrams.md](../../agent/02-get-agent-diagrams.md) |

---

## Tools

Attach = create on agent (`POST .../agents/{id}/tools`) or `PATCH .../tools/{id}` with `agent_id`.

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/agents/{agent_id}/tools` | **No** | **Yes** | Add optional `routing_hint: str \| None` (max 500) to `CreateToolRequest`. **Service:** after `push_tool_id`, upsert `agent.capability_catalog.tools[tool_id] = { routing_hint }`. Doc: [../../tools/01-create-tool-diagrams.md](../../tools/01-create-tool-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/tools` | **No** | **Optional** | **Optional:** include `routing_hint` on `ToolListItem` (read from agent catalog). |
| `GET` | `/api/v1/agents/{agent_id}/tools/{tool_id}` | **No** | **Optional** | **Optional:** include `routing_hint` on `GetToolResponse`. |
| `GET` | `/api/v1/tools` | **No** | **No** | **No API work.** |
| `PATCH` | `/api/v1/tools/{tool_id}` | **No** | **Yes** | Add optional `routing_hint` to `UpdateToolRequest`. **Service:** on attach (`agent_id` set) → upsert catalog entry; on detach (`agent_id: null`) → `$unset` catalog key + existing `pull_tool_id`; on move → remove from old agent catalog, add to new. |

**Route file:** `app/api/v1/agents.py`, `app/api/v1/tools.py` — **no new routes.**

---

## Knowledge bases

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `GET` | `/api/v1/agents/{agent_id}/knowledgebases` | **No** | **Optional** | **Optional:** `routing_hint` on list items. |
| `GET` | `/api/v1/knowledgebases` | **No** | **No** | **No API work.** |
| `POST` | `/api/v1/knowledgebases` | **No** | **Yes** | Add optional `routing_hint` to `CreateKnowledgebaseRequest`. When `agent_id` is set: upsert `capability_catalog.knowledge_bases[kb_id]` after create + `push_knowledge_base_id`. Doc: [../../knowledgebase/01-create-knowledgebase-diagrams.md](../../knowledgebase/01-create-knowledgebase-diagrams.md) |
| `PATCH` | `/api/v1/knowledgebases/{knowledgebase_id}` | **No** | **Yes** | Add optional `routing_hint` to `UpdateKnowledgebaseRequest`. Sync catalog on attach / detach / move (same pattern as tools). |

**Route file:** `app/api/v1/knowledgebases.py` — **no new routes.**

---

## Workflows

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `GET` | `/api/v1/workflows` | **No** | **No** | **No API work.** |
| `POST` | `/api/v1/workflows` | **No** | **Yes** | Add optional `routing_hint` to `CreateWorkflowRequest`. When `agent_id` set: upsert `capability_catalog.workflows[workflow_id]`. Doc: [../../workflows/01-create-workflow-diagrams.md](../../workflows/01-create-workflow-diagrams.md) |
| `GET` | `/api/v1/workflows/{workflow_id}` | **No** | **Optional** | **Optional:** `routing_hint` on response. |
| `PATCH` | `/api/v1/workflows/{workflow_id}` | **No** | **Yes** | Add optional `routing_hint` to `UpdateWorkflowRequest`. Sync catalog on `agent_id` attach/detach/move. |
| `POST` | `/api/v1/workflows/{workflow_id}/publish` | **No** | **No** | **No API work.** Publishing does not affect catalog. |

**Route file:** `app/api/v1/workflows.py` — **no new routes.**

---

## Sub-agents

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/agents/{agent_id}/sub-agents` | **No** | **Yes** | Add optional `routing_hint` to `CreateSubAgentRequest`. **Service:** after create + `push_sub_agent_id`, upsert `capability_catalog.sub_agents[sub_agent_id]`. Doc: [../../sub-agents/01-create-sub-agent-diagrams.md](../../sub-agents/01-create-sub-agent-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents` | **No** | **Optional** | **Optional:** `routing_hint` on `SubAgentListItem`. |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | **No** | **Optional** | **Optional:** `routing_hint` on `GetSubAgentResponse`. |
| `PATCH` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | **No** | **Yes** | Add optional `routing_hint` to `UpdateSubAgentRequest`. Update catalog entry without re-creating sub-agent. |

**Route file:** `app/api/v1/agents.py` — **no new routes.**

---

## Connectors, executors, auth, health

Unrelated to capability catalog or chat prompt assembly.

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/connectors` | **No** | **No** | **No API work.** Doc: [../../connectors/01-create-connector-diagrams.md](../../connectors/01-create-connector-diagrams.md) |
| `GET` | `/api/v1/connectors` | **No** | **No** | **No API work.** |
| `GET` | `/api/v1/connectors/{connector_id}` | **No** | **No** | **No API work.** |
| `PATCH` | `/api/v1/connectors/{connector_id}` | **No** | **No** | **No API work.** |
| `DELETE` | `/api/v1/connectors/{connector_id}` | **No** | **No** | **No API work.** |
| `GET` | `/api/v1/connector-types` | **No** | **No** | **No API work.** Doc: [../../connectors/00-connector-types-catalog.md](../../connectors/00-connector-types-catalog.md) |
| `GET` | `/api/v1/executors` | **No** | **No** | **No API work.** Doc: [../../tools/00-executor-catalog.md](../../tools/00-executor-catalog.md) |
| `POST` | `/api/v1/auth/register` | **No** | **No** | **No API work.** |
| `POST` | `/api/v1/auth/resend-verification` | **No** | **No** | **No API work.** |
| `POST` | `/api/v1/auth/verify-email` | **No** | **No** | **No API work.** |
| `GET` | `/api/v1/auth/me` | **No** | **No** | **No API work.** |
| `GET` | `/api/v1/health` | **No** | **No** | **No API work.** |

---

## Shared schema: `routing_hint`

Add to create/update requests for attachable resources (tools, KBs, workflows, sub-agents):

```python
routing_hint: str | None = Field(default=None, max_length=500)
```

**Stored on agent (not on tool/KB document):**

```json
{
  "capability_catalog": {
    "tools": { "<tool_id>": { "routing_hint": "Use when user asks about balance" } },
    "knowledge_bases": { "<kb_id>": { "routing_hint": "Product FAQ" } },
    "workflows": { "<workflow_id>": { "routing_hint": "Greet new users" } },
    "sub_agents": { "<sub_agent_id>": { "routing_hint": "Escalate billing" } }
  }
}
```

**Rules:**

- Never write hints into `agent.system_prompt`.
- Detach resource → remove id from `*_ids` **and** remove catalog key.
- Chat runtime reads catalog + live `RuntimeBundle` to build layer **[3]**.

Runtime assembly: [runtime-migration-agentic.md](./runtime-migration-agentic.md).

---

## New APIs

### Required for minimum migration

**None.** Existing attach/detach endpoints + schema fields are sufficient.

### Optional (builder UI)

| Method | Path | Purpose |
|--------|------|---------|
| `PATCH` | `/api/v1/agents/{agent_id}/capability-catalog` | Bulk edit `routing_hint` entries without PATCH on each tool/KB/workflow/sub-agent. |

**Request body (proposed):**

```json
{
  "tools": { "<tool_id>": { "routing_hint": "..." } },
  "knowledge_bases": {},
  "workflows": {},
  "sub_agents": {}
}
```

**When to add:** only if frontend needs a dedicated “routing hints” screen. Otherwise defer.

### Not a REST API (Phase C)

`search_knowledge` is an **LLM tool** inside `OrchestratorRunner`, not a new HTTP endpoint. Layer **[4]** `rag_context` is injected only after that tool runs.

---

## Route files — edit checklist

| File | New endpoints? | Action |
|------|:--------------:|--------|
| `app/api/v1/chat.py` | No | **No change** |
| `app/api/v1/agents.py` | No | **No change** (optional GET catalog via schema only) |
| `app/api/v1/tools.py` | No | **No change** |
| `app/api/v1/knowledgebases.py` | No | **No change** |
| `app/api/v1/workflows.py` | No | **No change** |
| `app/api/v1/connectors.py` | No | **No change** |
| `app/api/v1/executors.py` | No | **No change** |
| `app/api/v1/auth.py` | No | **No change** |
| `app/api/v1/health.py` | No | **No change** |

---

## Schema files — edit checklist

| File | Change |
|------|--------|
| `app/schemas/tool.py` | **Yes** — `routing_hint` on `CreateToolRequest`, `UpdateToolRequest`; optional on responses |
| `app/schemas/knowledgebase.py` | **Yes** — `routing_hint` on create/update; optional on responses |
| `app/schemas/workflow.py` | **Yes** — `routing_hint` on create/update; optional on responses |
| `app/schemas/sub_agent.py` | **Yes** — `routing_hint` on create/update; optional on responses |
| `app/schemas/agent.py` | **Optional** — `capability_catalog` on `GetAgentResponse` |
| `app/schemas/chat.py` | **No** |
| `app/schemas/preview.py` | **No** |
| `app/schemas/connector.py` | **No** |
| `app/schemas/auth.py` | **No** |

---

## Service / repository (not REST, but required)

| Component | Change |
|-----------|--------|
| `app/services/agent_service.py` | Init empty `capability_catalog` on create |
| `app/services/tool_service.py` | Catalog sync on create / attach / detach |
| `app/services/knowledgebase_service.py` | Catalog sync |
| `app/services/workflow_service.py` | Catalog sync |
| `app/services/sub_agent_service.py` | Catalog sync |
| `app/infrastructure/db/repositories/mongo/agent_repository.py` | Helpers: `upsert_catalog_entry`, `remove_catalog_entry` (or inline `$set` / `$unset`) |
| `app/services/chat_completion_service.py` | **No API change** — use `FinalPromptBuilder`; stop mutating `system_prompt` for guardrails |
| `app/services/runtime_bundle_loader.py` | Load `capability_catalog` into `RuntimeBundle` |

---

## Implementation order (API-facing)

1. **Mongo + agent create** — empty `capability_catalog`
2. **Schemas** — `routing_hint` on attachable create/update
3. **Services** — sync catalog on attach/detach
4. **Runtime** — `FinalPromptBuilder` at chat (no REST change)
5. **Optional** — expose catalog on `GET /agents/{id}`; optional `PATCH capability-catalog`
6. **Phase C** — agentic RAG tool (no new REST)

---

## Runtime (non-REST)

Code changes for `FinalPromptBuilder`, catalog builder, chat graph: [runtime-migration-agentic.md](./runtime-migration-agentic.md)
