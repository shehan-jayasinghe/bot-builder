# Update Workflow — attach / detach / move — `PATCH /api/v1/workflows/{workflow_id}`

**Agentic migration:** [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md) — optional `routing_hint` on PATCH when `agent_id` is set; stored in `agent.capability_catalog.workflows`.

Create workflow: [01-create-workflow-diagrams.md](./01-create-workflow-diagrams.md)

---

## Request body (agentic fields)

| Field | When set | Effect |
|-------|----------|--------|
| `agent_id` | attach / detach / move | Updates `workflow.agent_id` and syncs `agent.workflow_ids` |
| `routing_hint` | optional | Upserts or clears hint in `agent.capability_catalog.workflows[workflow_id]` |
| `name`, `description`, `nodes`, `edges` | content edit | Unrelated to catalog; may revert `published` → `draft` |

```json
{
  "agent_id": "6a3b7c61d8139334274fbbf1",
  "routing_hint": "Greet new users on first message"
}
```

Detach:

```json
{ "agent_id": null }
```

`POST /api/v1/workflows/{workflow_id}/publish` does **not** change the capability catalog.

---

## Catalog rules

| Action | `workflow_ids` | `capability_catalog.workflows` |
|--------|----------------|--------------------------------|
| Attach | `push_workflow_id` | upsert entry |
| Detach | `pull_workflow_id` | `$unset` entry |
| Move A → B | pull A, push B | remove from A; upsert on B |
| Move without `routing_hint` | — | **preserves** hint from source agent |

---

## Navigate to files

| Step | File |
|------|------|
| API route | [workflows.py](../../app/api/v1/workflows.py) |
| Service | [workflow_service.py](../../app/services/workflow_service.py) |
| Schema | [workflow.py](../../app/schemas/workflow.py) — `UpdateWorkflowRequest` |
| Catalog helpers | [capability_catalog.py](../../app/domain/models/capability_catalog.py) |
| Repository | [agent_repository.py](../../app/infrastructure/db/repositories/mongo/agent_repository.py) |

---

## List with hints

`GET /api/v1/workflows?agent_id={id}` returns `routing_hint` on each item. Single workflow: `GET /api/v1/workflows/{workflow_id}` includes hint when attached.
