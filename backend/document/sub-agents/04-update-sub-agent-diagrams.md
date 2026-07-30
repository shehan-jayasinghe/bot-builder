# Update Sub-Agent — `PATCH /api/v1/agents/{agent_id}/sub-agents/{sub_agent_id}`

**Agentic migration:** Phase A **Done**. Phase B **no REST change**. Phase C **Done** — sub-agent chat RAG via `search_knowledge`. Phase D **Done** — sticky sub-agent at chat (no REST change). See [../agentic/updets/api-migration-agentic-phase-d.md](../agentic/updets/api-migration-agentic-phase-d.md). **LangChain proper (Done, no REST change):** [../agentic/updets/migration-langchain-proper.md](../agentic/updets/migration-langchain-proper.md).

Create sub-agent: [01-create-sub-agent-diagrams.md](./01-create-sub-agent-diagrams.md)

---

## Request body (agentic fields)

| Field | When set | Effect |
|-------|----------|--------|
| `routing_hint` | optional | Upserts or clears hint in `agent.capability_catalog.sub_agents[sub_agent_id]` |
| `name`, `instructions`, `tool_ids`, etc. | content edit | Updates sub-agent document only |

Sub-agents are **always scoped to one parent agent** — there is no `agent_id` move on PATCH (unlike tools/KBs/workflows).

```json
{
  "routing_hint": "Escalate billing and payment disputes"
}
```

Clear hint:

```json
{ "routing_hint": null }
```

---

## Service flow

```mermaid
flowchart TB
    PATCH[PATCH sub-agents/sub_agent_id]
    PATCH --> UPDATE[SubAgentService.update]
    UPDATE --> FIELDS{routing_hint in body?}
    FIELDS -->|yes| UPSERT[upsert_capability_catalog_entry]
    FIELDS -->|no| SKIP[No catalog change]
    UPSERT --> RESP[Return with routing_hint from catalog]
    SKIP --> RESP
```

---

## Navigate to files

| Step | File |
|------|------|
| API route | [agents.py](../../app/api/v1/agents.py) |
| Service | [sub_agent_service.py](../../app/services/sub_agent_service.py) |
| Schema | [sub_agent.py](../../app/schemas/sub_agent.py) — `UpdateSubAgentRequest` |
| Repository | [agent_repository.py](../../app/infrastructure/db/repositories/mongo/agent_repository.py) |

---

## List with hints

`GET /api/v1/agents/{agent_id}/sub-agents` and `GET .../sub-agents/{sub_agent_id}` return `routing_hint` from the parent agent catalog.
