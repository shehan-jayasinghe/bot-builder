# Update Workflow — `PATCH /api/v1/workflows/{workflow_id}`

Partially update a workflow. Used by the editor **Save** button — persists title, canvas `nodes` / `edges`, and optional `description`.

Model reference: [00-workflow-model.md](./00-workflow-model.md)

**Not in MVP:** `status` → `published` (Publish button disabled).

---

# Flow 1 — Auth

Same as [03-get-workflow-diagrams.md](./03-get-workflow-diagrams.md) Flow 1.

```mermaid
flowchart TB
    REQ[PATCH /api/v1/workflows/workflow_id]
    REQ --> API[API route]
    API --> DI[get_current_user]
    DI --> JWT[JWT verify]
    JWT -->|invalid| E401[401]
    JWT --> DB[user + org]
    DB --> F2[Flow 2]
```

---

# Flow 2 — Validate path + load existing

```mermaid
flowchart TB
    AUTH[CurrentUser — organization_id]

    AUTH --> PATH[workflow_id]

    subgraph PATHVAL["Path + ownership"]
        P1[Validate ObjectId]
        P2[WorkflowRepository — find by id + org]
        P3{exists?}
        P1 --> P2 --> P3
    end

    PATH --> PATHVAL
    PATHVAL -->|invalid id| E422[422]
    PATHVAL -->|missing| E404[404 Workflow not found]
    P3 --> F3[Flow 3]
```

---

# Flow 3 — Validate request body (partial)

All fields optional — only sent fields are updated. At least one field required.

```mermaid
flowchart TB
    EXIST[Existing workflow loaded]

    EXIST --> BODY[JSON body]

    subgraph VALIDATE["Pydantic — UpdateWorkflowRequest"]
        V1[name — 1–200 chars]
        V2[description — max 2000 or null]
        V3[agent_id — ObjectId or null]
        V4[nodes — array]
        V5[edges — array]
        V1 --> V2 --> V3 --> V4 --> V5
    end

    BODY --> VALIDATE
    VALIDATE -->|invalid| E422[422]
    VALIDATE -->|empty body| E422
    VALIDATE --> AGENT

    subgraph AGENT["Optional agent check"]
        A1{agent_id sent and not null?}
        A2[Agent exists in org]
        A1 -->|no| SAVE
        A1 -->|yes| A2
        A2 -->|missing| E404A[404 Agent not found]
    end

    AGENT --> SAVE

    subgraph SAVE["Persist"]
        S1[WorkflowRepository.update]
        S2[Set updated_at]
        S1 --> S2
    end

    SAVE --> RES[200 UpdateWorkflowResponse]
```

### Updatable fields (MVP)

| Field | Rule |
|-------|------|
| `name` | optional — user edits title in editor |
| `description` | optional |
| `agent_id` | optional — set or clear (`null`) |
| `nodes` | optional — full canvas node array |
| `edges` | optional — full canvas edge array |

### Immutable via PATCH (MVP)

| Field | Reason |
|-------|--------|
| `organization_id` | From auth only |
| `status` | Publish flow — phase 2 |
| `id` | Path param |

---

# Request body examples

**Save title + canvas (toolbar Save)**

```http
PATCH /api/v1/workflows/6a3f9012d8139334274fbc00
Authorization: Bearer <clerk_jwt>
Content-Type: application/json

{
  "name": "Customer onboarding",
  "nodes": [
    {
      "id": "start-1",
      "type": "start",
      "position": { "x": 120, "y": 220 },
      "data": {}
    },
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 300, "y": 220 },
      "data": { "label": "Customer name" }
    },
    {
      "id": "message-1",
      "type": "message",
      "position": { "x": 500, "y": 220 },
      "data": { "text": "Hello {{name}}" }
    }
  ],
  "edges": [
    { "id": "edge-1", "source": "start-1", "target": "input-1" },
    { "id": "edge-2", "source": "input-1", "target": "message-1" }
  ]
}
```

**Rename only**

```json
{ "name": "Billing flow" }
```

---

# Response `200`

Same shape as [03-get-workflow-diagrams.md](./03-get-workflow-diagrams.md) — full workflow document with new `updated_at`.

---

# Error responses

| Status | When |
|--------|------|
| `401` | Invalid JWT |
| `404` | Workflow or agent not found |
| `422` | Invalid body, empty PATCH, or bad ObjectId |

---

# Auto-save (phase 2)

MVP uses manual **Save** only. `auto_save` toggle in UI is visual-only until debounced `PATCH` is implemented.

---

# Navigate to planned files

| What | Open file |
|------|-----------|
| API route | [workflows.py](../../app/api/v1/workflows.py) *(planned)* |
| Service | [workflow_service.py](../../app/services/workflow_service.py) *(planned)* |
| Repository | [workflow_repository.py](../../app/infrastructure/db/repositories/mongo/workflow_repository.py) *(planned)* |
| Update schema | [workflow.py](../../app/schemas/workflow.py) *(planned)* |
| Frontend Save handler | [WorkflowEditorPage.tsx](../../../frontend/src/pages/workflows/WorkflowEditorPage.tsx) *(planned)* |
