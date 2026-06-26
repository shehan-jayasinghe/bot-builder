# Workflow Model — launch MVP

Organization-scoped **conversation flows** — visual canvas of nodes and edges saved as JSON.

Used by the **Workflows** sidebar list and the workflow editor (`/workflows/new`, `/workflows/{workflow_id}`).

`organization_id` comes from JWT auth (`CurrentUser`), not the request body.

Related API docs:

- Create: [01-create-workflow-diagrams.md](./01-create-workflow-diagrams.md)
- List: [02-list-workflows-diagrams.md](./02-list-workflows-diagrams.md)
- Get: [03-get-workflow-diagrams.md](./03-get-workflow-diagrams.md)
- Update (Save): [04-update-workflow-diagrams.md](./04-update-workflow-diagrams.md)

---

# Launch limits (MVP)

| Rule | Value |
|------|-------|
| Max workflows per organization | **5** |
| Default name on create | `Welcome` |
| `description` | optional |
| `agent_id` | optional — not required for MVP |
| Publish | **not in MVP** — `status` stays `draft`; Publish button disabled in UI |

---

# MongoDB collection: `workflows`

```json
{
  "_id": "6a3f9012d8139334274fbc00",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "name": "Welcome",
  "description": null,
  "agent_id": null,
  "status": "draft",
  "nodes": [
    {
      "id": "start-1",
      "type": "start",
      "position": { "x": 120, "y": 220 },
      "data": {}
    },
    {
      "id": "message-1",
      "type": "message",
      "position": { "x": 320, "y": 220 },
      "data": { "text": "Welcome" }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "start-1",
      "target": "message-1"
    }
  ],
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `organization_id` | yes | From `CurrentUser` — never in request body |
| `name` | yes | 1–200 chars; default `Welcome` |
| `description` | no | Max 2000 chars |
| `agent_id` | no | Optional link to an agent — 24-char ObjectId when set |
| `status` | yes | `draft` (MVP only); `published` — phase 2 |
| `nodes` | yes | Canvas nodes — may be empty array on create |
| `edges` | yes | Canvas connections — may be empty array on create |
| `created_at` | yes | Set on insert |
| `updated_at` | yes | Updated on every save |

---

# Node types (MVP palette)

Toolbar buttons map to node `type` values the editor can add to the canvas.

| Palette label | `type` | Purpose |
|---------------|--------|---------|
| *(auto)* | `start` | Entry point — one per workflow recommended |
| Input | `input` | Collect user input |
| Output | `output` | Send response to user |
| Actions | `action` | Run step (KB query, integration, etc.) — subtype in `data` |
| Dev | `dev` | Debug / test step |
| Message | `message` | Static or templated message bubble |

### `message` node `data`

```json
{ "text": "Welcome" }
```

### `action` node `data` (MVP stub)

```json
{
  "action_type": "kb_query",
  "label": "KB Query"
}
```

Action subtypes (palette dropdown — phase 2 runtime):

| `action_type` | Label |
|---------------|-------|
| `kb_query` | KB Query |
| `integration` | Integration |
| `http` | HTTP |

---

# API endpoints (MVP)

| Method | Path | Doc |
|--------|------|-----|
| `POST` | `/api/v1/workflows` | [01-create-workflow-diagrams.md](./01-create-workflow-diagrams.md) |
| `GET` | `/api/v1/workflows` | [02-list-workflows-diagrams.md](./02-list-workflows-diagrams.md) |
| `GET` | `/api/v1/workflows/{workflow_id}` | [03-get-workflow-diagrams.md](./03-get-workflow-diagrams.md) |
| `PATCH` | `/api/v1/workflows/{workflow_id}` | [04-update-workflow-diagrams.md](./04-update-workflow-diagrams.md) |

**Not in MVP:** `DELETE`, publish endpoint, workflow execution runtime.

---

# UI mapping

| UI | API |
|----|-----|
| Sidebar **+ Create** | `POST /workflows` → navigate to `/workflows/{id}` |
| Sidebar workflow list | `GET /workflows` |
| Editor title (editable) | `PATCH /workflows/{id}` — `name` |
| Toolbar **Save** | `PATCH /workflows/{id}` — `name`, `nodes`, `edges`, optional `description` |
| Canvas drag/drop | Local state until Save → `nodes`, `edges` in PATCH body |
| **Publish** | Disabled in MVP |

---

# Navigate to implementation files

| Layer | Open file |
|-------|-----------|
| API routes | [workflows.py](../../app/api/v1/workflows.py) |
| Router mount | [router.py](../../app/api/v1/router.py) |
| Schemas | [workflow.py](../../app/schemas/workflow.py) |
| Service | [workflow_service.py](../../app/services/workflow_service.py) |
| Repository | [workflow_repository.py](../../app/infrastructure/db/repositories/mongo/workflow_repository.py) |
| Frontend editor | [WorkflowEditorPage.tsx](../../../frontend/src/pages/workflows/WorkflowEditorPage.tsx) *(planned)* |
| Frontend sidebar | [Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx) |
