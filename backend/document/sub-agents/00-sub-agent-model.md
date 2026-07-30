# Sub Agent Model — launch MVP

A **Sub Agent** is a delegatable specialist owned by a **parent agent**. It is not a full application/agent record — it is a lightweight config the parent LLM can route to at chat time (runtime delegation is phase 2).

Used by the agent detail **Sub Agents** tab and the **Add Sub Agent** modal.

`organization_id` comes from JWT auth (`CurrentUser`), not the request body.  
`agent_id` is the parent agent — set from the path param, not chosen freely in the body.

Related docs:

- Create: [01-create-sub-agent-diagrams.md](./01-create-sub-agent-diagrams.md)

---

# What a sub-agent is

| Concept | Meaning |
|---------|---------|
| **Parent agent** | Main orchestrator (`agents` collection) |
| **Sub agent** | Named specialist with its own instructions and scoped capabilities |
| **Delegation** | Parent LLM calls sub-agent by name + parameters (phase 2 runtime) |

```text
Parent Agent
  ├── system_prompt, personality, tone
  ├── tools / knowledge bases / workflows (global)
  └── sub_agent_ids[]
        └── Sub Agent (research_agent)
              ├── description → when to delegate
              ├── instructions → sub-agent system prompt
              ├── tool_ids / knowledge_base_ids / workflow_ids
              └── parameters[] → inputs for delegation
```

There is **no separate Skills collection**. UI label **Skills** maps to **tools**, **knowledge bases**, and **workflows** attached to the sub-agent (same three capability types as the parent).

---

# Launch limits (MVP)

| Rule | Value |
|------|-------|
| Max sub-agents per parent agent | **10** |
| `name` | `snake_case`, unique per parent agent |
| `instructions` | required, min 20 chars |
| `description` | optional, max 2000 chars |
| Capability IDs on sub-agent | must exist in org; MVP: must also be attached to **parent** agent |
| Runtime delegation | **not in MVP** — CRUD + UI only |

---

# MongoDB collection: `sub_agents`

```json
{
  "_id": "6a3f9012d8139334274fbc00",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "agent_id": "67agent001",
  "name": "research_agent",
  "description": "Delegates research tasks to a specialized agent.",
  "instructions": "You are a research assistant. Answer using attached knowledge bases and tools only.",
  "tool_ids": ["6a3f9012d8139334274fbc01"],
  "knowledge_base_ids": ["6a3f9012d8139334274fbc02"],
  "workflow_ids": [],
  "parameters": [
    {
      "name": "query",
      "type": "string",
      "description": "The research question to answer",
      "required": true
    }
  ],
  "status": "active",
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `organization_id` | yes | From `CurrentUser` — never in request body |
| `agent_id` | yes | Parent agent — 24-char ObjectId from path |
| `name` | yes | `snake_case`, 1–100 chars, unique per `agent_id` |
| `description` | no | Max 2000 — when parent should delegate |
| `instructions` | yes | Sub-agent system prompt, 20–8000 chars |
| `tool_ids` | yes | Array — may be empty |
| `knowledge_base_ids` | yes | Array — may be empty |
| `workflow_ids` | yes | Array — may be empty |
| `parameters` | yes | Array — may be empty |
| `status` | yes | `active` or `disabled` — default `active` |
| `created_at` | yes | Set on insert |
| `updated_at` | yes | Updated on every save |

---

# Parent agent linkage

On create, push sub-agent id onto the parent agent document:

```json
{
  "sub_agent_ids": ["6a3f9012d8139334274fbc00"]
}
```

`AssistantLoader` already reads `sub_agent_ids` at chat load ([assistant_loader.py](../../app/services/assistant_loader.py)).  
`AgentService.create_draft` should initialize `sub_agent_ids: []` on new agents (planned).

---

# Parameter object

Each entry in `parameters` defines one input the parent passes when delegating.

```json
{
  "name": "query",
  "type": "string",
  "description": "The research question to answer",
  "required": true
}
```

| Field | Rule |
|-------|------|
| `name` | `snake_case`, unique within the sub-agent |
| `type` | MVP: `string`, `number`, `boolean` |
| `description` | optional, max 500 chars |
| `required` | boolean, default `true` |

Phase 2: `enum`, `object`, array types.

---

# UI mapping (Add Sub Agent modal)

| UI field | API / Mongo field |
|----------|-------------------|
| Sub Agent Name * | `name` |
| Description | `description` |
| Instructions | `instructions` |
| Skills (+ Add) | `tool_ids`, `knowledge_base_ids`, `workflow_ids` |
| Parameters (+ Add) | `parameters[]` |
| Save | `POST /agents/{agent_id}/sub-agents` |

Skills picker (MVP): choose from capabilities **already attached to the parent agent** (tools, KBs, workflows with `agent_id` = parent).

---

# API endpoints (MVP — planned)

| Method | Path | Doc |
|--------|------|-----|
| `POST` | `/api/v1/agents/{agent_id}/sub-agents` | [01-create-sub-agent-diagrams.md](./01-create-sub-agent-diagrams.md) |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents` | *(planned)* |
| `GET` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | *(planned)* |
| `PATCH` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | *(planned)* |
| `DELETE` | `/api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}` | *(planned)* |

Register `/{agent_id}/sub-agents` routes **before** `GET /{agent_id}` in [agents.py](../../app/api/v1/agents.py) *(planned)*.

---

# Runtime (phase 2 — not MVP)

1. Load parent `sub_agent_ids` at chat time.
2. Expose each sub-agent to the parent LLM as a function schema (`name`, `description`, `parameters`).
3. On delegate call → run sub-agent with `instructions` + its scoped tools / KB RAG.
4. Return result to parent LLM for the final reply.

---

# Navigate to planned implementation files

| Layer | Open file |
|-------|-----------|
| API routes | [agents.py](../../app/api/v1/agents.py) *(planned)* |
| Schemas | `sub_agent.py` in [schemas/](../../app/schemas/) *(planned)* |
| Service | `sub_agent_service.py` in [services/](../../app/services/) *(planned)* |
| Repository | `sub_agent_repository.py` in [repositories/mongo/](../../app/infrastructure/db/repositories/mongo/) *(planned)* |
| Exceptions | `sub_agent.py` in [shared/exceptions/](../../app/shared/exceptions/) *(planned)* |
| Frontend tab | [AgentDetailPage.tsx](../../../frontend/src/pages/agent/AgentDetailPage.tsx) *(planned)* |
