# API migration — agentic system (capability catalog)

Single reference for **every REST endpoint** affected by the move to an agentic runtime:

- Final prompt layers: `[1] system_prompt` (+ personality/tone at runtime) → `[2] guardrails` → `[3] capability_catalog` → `[4] rag_context` (**always-on today**; Phase C makes RAG tool-driven only)
- `routing_hint` on attachable resources → stored in `agent.capability_catalog` (not in `system_prompt`)

**Related specs:**

- [../00-overview.md](../00-overview.md)
- [runtime-migration-agentic.md](./runtime-migration-agentic.md)
- Phase B: [api-migration-agentic-phase-b.md](./api-migration-agentic-phase-b.md) · [runtime-migration-agentic-phase-b.md](./runtime-migration-agentic-phase-b.md)
- Phase C: [api-migration-agentic-phase-c.md](./api-migration-agentic-phase-c.md) · [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md)

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
| `POST` | `/api/v1/agents` | **No** | **No** *(response)* | **Done.** `create_draft` inits empty `capability_catalog`. Doc: [../../agent/01-create-agent-diagrams.md](../../agent/01-create-agent-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}` | **No** | **Optional Yes** | **Optional:** add `capability_catalog` to `GetAgentResponse` so builder UI can edit hints. Not required for Phase A if hints are set only via attach APIs. Doc: [../../agent/02-get-agent-diagrams.md](../../agent/02-get-agent-diagrams.md) |

---

## Tools

Attach = create on agent (`POST .../agents/{id}/tools`) or `PATCH .../tools/{id}` with `agent_id`.

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/agents/{agent_id}/tools` | **No** | **Yes** | **Done.** Doc: [../../tools/01-create-tool-diagrams.md](../../tools/01-create-tool-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/tools` | **No** | **Optional** | **Done:** `routing_hint` on `ToolListItem` (from agent catalog). |
| `GET` | `/api/v1/agents/{agent_id}/tools/{tool_id}` | **No** | **Optional** | **Done:** `routing_hint` on `GetToolResponse`. |
| `GET` | `/api/v1/tools` | **No** | **Optional** | **Done:** `routing_hint` on list items when `?agent_id=` filter is set. Without filter, hint is omitted. |
| `PATCH` | `/api/v1/tools/{tool_id}` | **No** | **Yes** | **Done.** `routing_hint` on `UpdateToolRequest`. Catalog sync on attach/detach/move. Doc: [../../tools/08-update-tool-agent-diagrams.md](../../tools/08-update-tool-agent-diagrams.md) |

**Route file:** `app/api/v1/agents.py`, `app/api/v1/tools.py` — **no new routes.**

---

## Knowledge bases

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `GET` | `/api/v1/agents/{agent_id}/knowledgebases` | **No** | **Optional** | **Done:** `routing_hint` on list items. |
| `GET` | `/api/v1/knowledgebases` | **No** | **Optional** | **Done:** `routing_hint` when `?agent_id=` filter is set. |
| `POST` | `/api/v1/knowledgebases` | **No** | **Yes** | **Done.** Doc: [../../knowledgebase/01-create-knowledgebase-diagrams.md](../../knowledgebase/01-create-knowledgebase-diagrams.md) |
| `PATCH` | `/api/v1/knowledgebases/{knowledgebase_id}` | **No** | **Yes** | **Done.** Doc: [../../knowledgebase/04-update-knowledgebase-agent-diagrams.md](../../knowledgebase/04-update-knowledgebase-agent-diagrams.md) |

**Route file:** `app/api/v1/knowledgebases.py` — **no new routes.**

---

## Workflows

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `GET` | `/api/v1/workflows` | **No** | **Optional** | **Done:** `routing_hint` when `?agent_id=` filter is set. |
| `POST` | `/api/v1/workflows` | **No** | **Yes** | **Done.** Doc: [../../workflows/01-create-workflow-diagrams.md](../../workflows/01-create-workflow-diagrams.md) |
| `GET` | `/api/v1/workflows/{workflow_id}` | **No** | **Optional** | **Done:** `routing_hint` when workflow is attached to an agent. |
| `PATCH` | `/api/v1/workflows/{workflow_id}` | **No** | **Yes** | **Done.** Doc: [../../workflows/04-update-workflow-diagrams.md](../../workflows/04-update-workflow-diagrams.md) |
| `POST` | `/api/v1/workflows/{workflow_id}/publish` | **No** | **No** | **No API work.** Publishing does not affect catalog. |

**Route file:** `app/api/v1/workflows.py` — **no new routes.**

---

## Sub-agents

| Method | Path | Route change | Schema change | What to do |
|--------|------|:------------:|:-------------:|------------|
| `POST` | `/api/v1/agents/{agent_id}/sub-agents` | **No** | **Yes** | **Done.** Doc: [../../sub-agents/01-create-sub-agent-diagrams.md](../../sub-agents/01-create-sub-agent-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents` | **No** | **Optional** | **Done:** `routing_hint` on `SubAgentListItem`. |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | **No** | **Optional** | **Done:** `routing_hint` on `GetSubAgentResponse`. |
| `PATCH` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | **No** | **Yes** | **Done.** Doc: [../../sub-agents/04-update-sub-agent-diagrams.md](../../sub-agents/04-update-sub-agent-diagrams.md) |

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
- Move resource between agents **without** `routing_hint` in PATCH → **preserve** existing hint on the target agent.
- Re-PATCH the same `agent_id` without `routing_hint` → no catalog upsert (avoids wiping hint).
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

`search_knowledge` is an **LLM tool** inside `OrchestratorRunner`, not a new HTTP endpoint. Today layer **[4]** uses always-on `RAGRetriever` before orchestrator; Phase C replaces that with tool-driven retrieval only.

**Spec:** [api-migration-agentic-phase-c.md](./api-migration-agentic-phase-c.md) · [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md)

---

## Post–Phase A fixes (implemented)

| Fix | Where |
|-----|--------|
| Stored `system_prompt` = base role/responsibilities only (no baked personality/tone/guardrails) | [prompt_builder.py](../../app/infrastructure/ai/prompt_builder.py) |
| Personality, tone, guardrails added at chat via `FinalPromptBuilder` | [final_prompt_builder.py](../../app/domain/pipeline/prompt/final_prompt_builder.py) |
| Legacy agents with baked prompts — skip duplicate layers if markers already in `system_prompt` | `FinalPromptBuilder` baked-content detection |
| Preserve `routing_hint` on tool/KB/workflow move | `resolve_routing_hint_for_upsert` in [capability_catalog.py](../../app/domain/models/capability_catalog.py) |
| Skip catalog upsert on same-agent re-PATCH | `should_sync_catalog_on_agent_change` |
| Org list endpoints return hints when `?agent_id=` | tool / KB / workflow services |

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
| `app/infrastructure/db/repositories/mongo/agent_repository.py` | `upsert_capability_catalog_entry`, `remove_capability_catalog_entry` |
| `app/services/chat_completion_service.py` | **No API change** — use `FinalPromptBuilder`; stop mutating `system_prompt` for guardrails |
| `app/services/runtime_bundle_loader.py` | Load `capability_catalog` into `RuntimeBundle` |

---

## Implementation order (API-facing)

1. ~~**Mongo + agent create** — empty `capability_catalog`~~ **Done**
2. ~~**Schemas** — `routing_hint` on attachable create/update~~ **Done**
3. ~~**Services** — sync catalog on attach/detach~~ **Done**
4. ~~**Runtime** — `FinalPromptBuilder` at chat (no REST change)~~ **Done**
5. **Optional** — expose catalog on `GET /agents/{id}`; optional `PATCH capability-catalog`
6. ~~**Phase B** — agentic workflow routing (no REST)~~ **Done** — [api-migration-agentic-phase-b.md](./api-migration-agentic-phase-b.md)
7. **Phase C** — agentic RAG tool (no new REST) — [api-migration-agentic-phase-c.md](./api-migration-agentic-phase-c.md)

---

## Runtime (non-REST)

Code changes for `FinalPromptBuilder`, catalog builder, chat graph: [runtime-migration-agentic.md](./runtime-migration-agentic.md)
