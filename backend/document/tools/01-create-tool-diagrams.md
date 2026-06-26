# Create Tool — `POST /api/v1/agents/{agent_id}/tools`

Organization creates a **Tool** — JSON config that tells the platform which **executor** to run, which **connector** to use, and operation-specific **config**.

`organization_id` comes from JWT auth (`CurrentUser`), not the request body.

Executor catalog: [00-executor-catalog.md](./00-executor-catalog.md)  
Connector docs: [../connectors/01-create-connector-diagrams.md](../connectors/01-create-connector-diagrams.md)

---

# Tool document shape

```json
{
  "name": "customer_lookup",
  "description": "Retrieve customer loyalty information",
  "executor": "mongo_find_one",
  "connector_id": "6a3f8c12d8139334274fbbfe",
  "config": {
    "collection": "customers",
    "filter": { "customer_id": "{{customer_id}}" },
    "projection": ["name", "loyalty_points", "tier"]
  }
}
```

| Field | Source |
|-------|--------|
| `executor` | Platform catalog — [00-executor-catalog.md](./00-executor-catalog.md) |
| `connector_id` | Org connector — [../connectors/](../connectors/) |
| `config` | Per-executor schema — operation details |
| `description` | Helps LLM decide when to call the tool |

---

# Flow 1 — Auth

Same as connectors and knowledge bases.

## Flow

```mermaid
flowchart TB
    REQ[Frontend request — POST /api/v1/agents/agent_id/tools]

    REQ --> API[API route]

    API --> DI[FastAPI Depends — get_current_user]

    subgraph JWT["JWT verification"]
        J1[Read Bearer token]
        J2[Verify signature with Clerk JWKS]
        J3[Get clerk_id from token]
        J1 --> J2 --> J3
    end

    DI --> JWT
    JWT -->|invalid| E401[401 Unauthorized]

    subgraph DB["Get user from DB"]
        D1[Find user by clerk_id]
        D2[Find organization]
        D3[Attach CurrentUser to request]
        D1 --> D2 --> D3
    end

    JWT -->|valid| DB
    DB --> F2[Continue to Flow 2]
```

## Navigate to auth files

| Flow step | What happens | Open file |
|-----------|--------------|-----------|
| API route | `POST /api/v1/agents/{agent_id}/tools` | [agents.py](../../app/api/v1/agents.py) *(planned)* |
| Router | Mount under `/api/v1` | [router.py](../../app/api/v1/router.py) |
| Depends | Inject `CurrentUser` | [auth.py](../../app/di/auth.py) |
| JWT + user + org | Same as KB / connectors | [clerk_authenticator.py](../../app/infrastructure/auth/clerk_authenticator.py) |

---

# Flow 2 — Validate agent

```mermaid
flowchart TB
    AUTH[CurrentUser — organization_id]

    AUTH --> PATH[Path param — agent_id]

    subgraph VALIDATE["Agent check"]
        V1[Validate agent_id — 24-char hex]
        V2[AgentRepository — find by id + organization_id]
        V3{exists?}
        V1 --> V2 --> V3
    end

    PATH --> VALIDATE
    VALIDATE -->|invalid id| E422[422]
    VALIDATE -->|not found| E404[404 Agent not found]
    V3 -->|yes| F3
```

Register `/{agent_id}/tools` **before** `/{agent_id}` in [agents.py](../../app/api/v1/agents.py) *(planned)*.

---

# Flow 3 — Validate request body

```mermaid
flowchart TB
    BODY[JSON — name, description, executor, connector_id, config]

    subgraph VALIDATE["Pydantic validation"]
        V1[name — snake_case, 1–100 chars]
        V2[description — 1–2000 chars]
        V3[executor — platform enum]
        V4[connector_id — 24-char hex]
        V5[config — per executor schema]
        V1 --> V2 --> V3 --> V4 --> V5
    end

    BODY --> VALIDATE
    VALIDATE -->|invalid| E422[422]
    VALIDATE --> UNIQUE

    subgraph UNIQUE["Uniqueness"]
        U1[Tool name unique per agent]
        U2{duplicate?}
        U1 --> U2
    end

    UNIQUE -->|yes| E409[409 Tool name exists]
    UNIQUE --> F4
```

### Pydantic validation rules

| Field | Rule |
|-------|------|
| `name` | required, snake_case `[a-z][a-z0-9_]*`, 1–100 chars, unique per agent |
| `description` | required, 1–2000 chars — shown to LLM as tool description |
| `executor` | required, must exist in [executor catalog](./00-executor-catalog.md) MVP list |
| `connector_id` | required for MVP executors |
| `config` | required object — validated by `executor` (discriminated union) |
| `organization_id` | **must not** be in body |

### Example requests

**Mongo — customer lookup**

```json
{
  "name": "customer_lookup",
  "description": "Get customer loyalty info when user asks about points or tier",
  "executor": "mongo_find_one",
  "connector_id": "6a3f8c12d8139334274fbbfe",
  "config": {
    "collection": "customers",
    "filter": { "customer_id": "{{customer_id}}" },
    "projection": ["name", "loyalty_points", "tier"]
  }
}
```

**HTTP — create invoice**

```json
{
  "name": "create_invoice",
  "description": "Create an invoice in the billing system",
  "executor": "http_request",
  "connector_id": "6a3f8c12d8139334274fbbff",
  "config": {
    "method": "POST",
    "path": "/invoices",
    "body": {
      "customer_id": "{{customer_id}}",
      "amount": "{{amount}}"
    }
  }
}
```

---

# Flow 4 — Validate connector + executor match

```mermaid
flowchart TB
    VALID[Body validated]

    VALID --> LOAD[ConnectorRepository — find by id + organization_id]

    LOAD -->|not found| E404[404 Connector not found]
    LOAD --> MATCH{connector.type matches executor?}

    MATCH -->|no| E422[422 — e.g. mongo_find_one needs mongo connector]
    MATCH -->|yes| F5
```

| Executor | Required `connector.type` |
|----------|---------------------------|
| `mongo_*` | `mongo` |
| `http_request` | `http` |

---

# Flow 5 — Save + attach to agent

```mermaid
flowchart TB
    READY[Validated]

    READY --> INSERT[ToolRepository.insert]

    subgraph DOC["tools collection"]
        D1[organization_id, agent_id]
        D2[name, description, executor, connector_id, config]
        D3[status = active]
        D4[created_at, updated_at]
        D1 --> D2 --> D3 --> D4
    end

    INSERT --> DOC
    DOC --> PUSH[AgentRepository — push tool id to tool_ids]
    PUSH --> RES[201 — CreateToolResponse]
```

**Mongo `tools` document:**

```json
{
  "_id": "6a3f9012d8139334274fbc00",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "agent_id": "67agent001",
  "name": "customer_lookup",
  "description": "Get customer loyalty info when user asks about points or tier",
  "executor": "mongo_find_one",
  "connector_id": "6a3f8c12d8139334274fbbfe",
  "config": {
    "collection": "customers",
    "filter": { "customer_id": "{{customer_id}}" },
    "projection": ["name", "loyalty_points", "tier"]
  },
  "status": "active",
  "created_at": "2026-06-25T12:00:00Z",
  "updated_at": "2026-06-25T12:00:00Z"
}
```

**Agent update:**

```json
{
  "tool_ids": ["6a3f9012d8139334274fbc00"]
}
```

Use `tool_ids` on agent (may alias existing `skill_ids` during migration).

**Response `201`:**

```json
{
  "id": "6a3f9012d8139334274fbc00",
  "name": "customer_lookup",
  "description": "Get customer loyalty info when user asks about points or tier",
  "executor": "mongo_find_one",
  "connector_id": "6a3f8c12d8139334274fbbfe",
  "config": {
    "collection": "customers",
    "filter": { "customer_id": "{{customer_id}}" },
    "projection": ["name", "loyalty_points", "tier"]
  },
  "status": "active",
  "agent_id": "67agent001",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "created_at": "2026-06-25T12:00:00Z",
  "updated_at": "2026-06-25T12:00:00Z"
}
```

## Error responses

| Status | When |
|--------|------|
| `401` | Invalid JWT |
| `404` | Agent or connector not found / wrong org |
| `409` | Tool `name` already exists on agent |
| `422` | Invalid body, config, or connector type mismatch |

---

# Navigate to planned files

| Layer | Open file |
|-------|-----------|
| API route | [agents.py](../../app/api/v1/agents.py) *(planned)* |
| Schemas | [tool.py](../../app/schemas/tool.py) *(planned)* |
| Service | [tool_service.py](../../app/services/tool_service.py) *(planned)* |
| Repository | [tool_repository.py](../../app/infrastructure/db/repositories/mongo/tool_repository.py) *(planned)* |
| Executor validation | [executor_catalog.py](../../app/domain/catalog/executor_catalog.py) *(planned)* |
| Config validation | [tool_config_schemas.py](../../app/schemas/tool_config.py) *(planned)* |
