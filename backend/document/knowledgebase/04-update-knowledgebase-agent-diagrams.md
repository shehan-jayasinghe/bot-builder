# Update Knowledge Base — attach / detach / move — `PATCH /api/v1/knowledgebases/{knowledgebase_id}`

**Agentic migration:** Phase A **Done**. Phase B **no REST change**. Phase C **planned** — `routing_hint` guides LLM `search_knowledge` at chat (no REST change). See [../agentic/updets/api-migration-agentic-phase-c.md](../agentic/updets/api-migration-agentic-phase-c.md).

Create KB: [01-create-knowledgebase-diagrams.md](./01-create-knowledgebase-diagrams.md)

---

## Request body (agentic fields)

| Field | When set | Effect |
|-------|----------|--------|
| `agent_id` | attach / detach / move | Updates `knowledgebase.agent_id` and syncs `agent.knowledge_base_ids` |
| `routing_hint` | optional | Upserts or clears hint in `agent.capability_catalog.knowledge_bases[kb_id]` |

```json
{
  "agent_id": "6a3b7c61d8139334274fbbf1",
  "routing_hint": "Product FAQ and policy questions"
}
```

Detach:

```json
{ "agent_id": null }
```

---

## Service flow

Same pattern as tools — see [../tools/08-update-tool-agent-diagrams.md](../tools/08-update-tool-agent-diagrams.md).

| Action | `knowledge_base_ids` | `capability_catalog.knowledge_bases` |
|--------|----------------------|--------------------------------------|
| Attach | `push_knowledge_base_id` | upsert entry |
| Detach | `pull_knowledge_base_id` | `$unset` entry |
| Move A → B | pull A, push B | remove from A; upsert on B |
| Move without `routing_hint` | — | **preserves** hint from source agent |

---

## Navigate to files

| Step | File |
|------|------|
| API route | [knowledgebases.py](../../app/api/v1/knowledgebases.py) |
| Service | [knowledgebase_service.py](../../app/services/knowledgebase_service.py) |
| Schema | [knowledgebase.py](../../app/schemas/knowledgebase.py) — `UpdateKnowledgebaseRequest` |
| Catalog helpers | [capability_catalog.py](../../app/domain/models/capability_catalog.py) |
| Repository | [agent_repository.py](../../app/infrastructure/db/repositories/mongo/agent_repository.py) |

---

## List with hints

`GET /api/v1/knowledgebases?agent_id={id}` returns `routing_hint` on each item. Agent-scoped list: `GET /api/v1/agents/{agent_id}/knowledgebases`.
