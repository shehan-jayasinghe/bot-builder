# Create Connector — `POST /api/v1/connectors`

Organization-scoped **connections** to external systems (customer MongoDB, REST API, SQL, etc.). Used later by **Tools** — a tool references `connector_id`; the org user never passes credentials in the tool JSON.

`organization_id` comes from JWT auth (`CurrentUser`), not from the request body.

**Agentic migration:** **No** API change for connector endpoints. See [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md). **LangChain proper (Done, no REST change):** [../agentic/updets/migration-langchain-proper.md](../agentic/updets/migration-langchain-proper.md).

**Not in scope:** platform infrastructure connectors (Bedrock, S3, Qdrant, Neo4j for KB ingest) — those stay in `.env` / platform config.

---

# Connector types (org-level)

| `type` | Label | MVP |
|--------|-------|-----|
| `mongo` | MongoDB | yes |
| `http` | REST / HTTP | yes |
| `sql` | SQL (PostgreSQL / MySQL) | phase 2 |
| `graphql` | GraphQL | phase 2 |
| `grpc` | gRPC | phase 2 |
| `redis` | Redis | phase 2 |
| `vector` | Vector DB (Qdrant, Pinecone, …) | phase 2 |

Full config schemas: [00-connector-types-catalog.md](./00-connector-types-catalog.md)

**Other connector routes** (`GET`, `PATCH`, `DELETE` `/api/v1/connectors/{id}`): **no agentic migration.** See [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md).

---

# Flow 1 — Auth

## Flow

```mermaid
flowchart TB
    REQ[Frontend request — POST /api/v1/connectors]

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
| API route | `POST /api/v1/connectors` handler | [connectors.py](../../app/api/v1/connectors.py) *(planned)* |
| Router | Mount connectors routes under `/api/v1` | [router.py](../../app/api/v1/router.py) |
| Depends | Inject `CurrentUser` | [auth.py](../../app/di/auth.py) |
| Read Bearer token | Parse `Authorization` header | [clerk_authenticator.py](../../app/infrastructure/auth/clerk_authenticator.py) |
| Verify JWT | Clerk JWKS signature check | [clerk_jwt.py](../../app/infrastructure/auth/clerk_jwt.py) |
| Get clerk_id | Read `sub` from token claims | [clerk_authenticator.py](../../app/infrastructure/auth/clerk_authenticator.py) |
| 401 Unauthorized | Invalid or expired token | [main.py](../../app/main.py) |
| Find user | Mongo lookup by `clerk_id` | [user_repository.py](../../app/infrastructure/db/repositories/mongo/user_repository.py) |
| Find organization | Mongo lookup by `organization_id` | [organization_repository.py](../../app/infrastructure/db/repositories/mongo/organization_repository.py) |
| Attach to request | Build `CurrentUser` | [current_user.py](../../app/domain/models/current_user.py) |

## JSON at each step

| Step | JSON |
|------|------|
| Start | `{}` |
| After JWT verification | `clerk_id`, `token_valid` |
| After user lookup | + `user_id`, `email` |
| After organization lookup | + `organization_id`, `organization_name` |
| Next | Flow 2 — validate request body |

**Start**

```json
{}
```

**After JWT verification** (+2 fields)

```json
{
  "clerk_id": "user_3FZX0ugQeNkL7VO8cMOY8mhRAS5",
  "token_valid": true
}
```

**After user lookup** (+2 fields)

```json
{
  "clerk_id": "user_3FZX0ugQeNkL7VO8cMOY8mhRAS5",
  "token_valid": true,
  "user_id": "6a3b7c61d8139334274fbbfd",
  "email": "jayasingheshehan1995@gmail.com"
}
```

**After organization lookup** (+2 fields)

```json
{
  "clerk_id": "user_3FZX0ugQeNkL7VO8cMOY8mhRAS5",
  "token_valid": true,
  "user_id": "6a3b7c61d8139334274fbbfd",
  "email": "jayasingheshehan1995@gmail.com",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "organization_name": "abc bank"
}
```

---

# Layer layout

```mermaid
flowchart TB
    subgraph API["API layer — Flows 1–2"]
        R[connectors.py — POST handler]
        SCH[Pydantic CreateConnectorRequest]
    end

    subgraph DI["DI layer"]
        AUTH[get_current_user]
        SVC[get_connector_service]
    end

    subgraph SERVICE["Service layer"]
        CS[ConnectorService.create]
    end

    subgraph VALIDATE["Validation layer"]
        CT[connector_constants — type enum]
        CFG[Per-type config schema — discriminated union]
    end

    subgraph TEST["Optional — Flow 3"]
        PING[Connector ping — mongo ping / HTTP health]
    end

    subgraph DATA["Data layer"]
        CR[ConnectorRepository → MongoDB connectors]
    end

    R --> AUTH --> SCH --> CS
    CS --> CT --> CFG
    CS --> PING
    CS --> CR
```

## Navigate to layer files

| Layer | What happens | Open file |
|-------|--------------|-----------|
| API route | `POST /api/v1/connectors` handler | [connectors.py](../../app/api/v1/connectors.py) *(planned)* |
| Router | Mount under `/api/v1` | [router.py](../../app/api/v1/router.py) |
| Pydantic | `CreateConnectorRequest` validation | [connector.py](../../app/schemas/connector.py) *(planned)* |
| Depends — auth | Inject `CurrentUser` | [auth.py](../../app/di/auth.py) |
| Depends — service | Inject `ConnectorService` | [connectors.py](../../app/di/connectors.py) *(planned)* |
| Service | Orchestrate validate → optional ping → Mongo | [connector_service.py](../../app/services/connector_service.py) *(planned)* |
| Type constants | `CONNECTOR_TYPE_MONGO`, `CONNECTOR_TYPE_HTTP`, … | [connector_constants.py](../../app/domain/constants/connector_constants.py) *(planned)* |
| Repository | Insert into `connectors` collection | [connector_repository.py](../../app/infrastructure/db/repositories/mongo/connector_repository.py) *(planned)* |
| Collection name | `connectors_collection` env | [config.py](../../app/config.py) *(planned)* |
| Repository DI | Wire Mongo repositories | [repositories.py](../../app/di/repositories.py) |

---

# Flow 2 — Validate request body

Runs after auth. Validates `name`, `type`, and type-specific `config`. Rejects unknown `type` or config fields that do not match the type.

## Flow

```mermaid
flowchart TB
    AUTH[CurrentUser — organization_id from auth]

    AUTH --> BODY[JSON body — name, type, config, test_connection?]

    subgraph VALIDATE["Pydantic validation"]
        V1[name — 1–200 chars]
        V2[type — connector type enum]
        V3{type?}
        V4[mongo config — uri, database]
        V5[http config — base_url, auth_type, …]
        V6[sql / graphql / grpc / redis / vector — phase 2]
        V1 --> V2 --> V3
        V3 -->|mongo| V4
        V3 -->|http| V5
        V3 -->|other| V6
    end

    BODY --> VALIDATE
    VALIDATE -->|invalid| E422[422 Validation error]

    VALIDATE --> UNIQUE

    subgraph UNIQUE["Uniqueness check"]
        U1[ConnectorRepository — find by name + organization_id]
        U2{name exists?}
        U1 --> U2
    end

    UNIQUE -->|duplicate name| E409[409 Connector name already exists]
    UNIQUE -->|ok| F3
```

## Navigate to Flow 2 files

| Flow step | What happens | Open file |
|-----------|--------------|-----------|
| Request validation | `CreateConnectorRequest` | [connector.py](../../app/schemas/connector.py) *(planned)* |
| 422 Validation error | Invalid body / wrong config for type | [connector.py](../../app/schemas/connector.py) *(planned)* |
| Type enum | `ConnectorType` StrEnum | [connector.py](../../app/schemas/connector.py) *(planned)* |
| Config models | `MongoConnectorConfig`, `HttpConnectorConfig`, … | [connector.py](../../app/schemas/connector.py) *(planned)* |
| 409 Conflict | Duplicate `name` per org | [connector_service.py](../../app/services/connector_service.py) *(planned)* |
| Org scoping | Never accept `organization_id` from client | [connector_service.py](../../app/services/connector_service.py) *(planned)* |

## Request body (frontend)

**MongoDB**

```json
{
  "name": "Customer MongoDB",
  "description": "Production customer database",
  "type": "mongo",
  "config": {
    "uri": "mongodb+srv://user:pass@cluster.example.net",
    "database": "customers"
  },
  "test_connection": true
}
```

**REST / HTTP — OAuth2 client credentials (Keycloak example)**

```json
{
  "name": "ShoutOUT Loyalty API",
  "description": "Loyalty REST service with Keycloak auth",
  "type": "http",
  "config": {
    "base_url": "https://api.loyalty.example.com",
    "auth_type": "oauth2_client_credentials",
    "token_url": "https://idp.loyalty.example.com/auth/realms/shoutout-loyalty-system/protocol/openid-connect/token",
    "client_id": "my-app-client",
    "client_secret": "...",
    "grant_type": "client_credentials"
  },
  "test_connection": true
}
```

**REST / HTTP — static bearer (dev only)**

```json
{
  "name": "Payments API",
  "description": "Internal billing REST service",
  "type": "http",
  "config": {
    "base_url": "https://api.example.com",
    "auth_type": "bearer",
    "auth_token": "sk_live_...",
    "default_headers": {
      "Accept": "application/json"
    }
  },
  "test_connection": true
}
```

### Pydantic validation rules

| Field | Rule |
|-------|------|
| `name` | required, 1–200 chars, unique per `organization_id` |
| `description` | optional, max 2000 chars |
| `type` | required enum: `mongo`, `http` (MVP); later: `sql`, `graphql`, `grpc`, `redis`, `vector` |
| `config` | required object — shape validated by `type` (discriminated union) |
| `test_connection` | optional bool, default `false` — when `true`, run Flow 3 before save |
| `organization_id` | **must not** appear in body — set from `CurrentUser` |

### Config rules by type (MVP)

| `type` | Required `config` fields |
|--------|--------------------------|
| `mongo` | `uri`, `database` |
| `http` | `base_url`; `auth_type` optional (`none`, `oauth2_client_credentials`, `api_key`, `basic`, `bearer`) |

### What the client does NOT send

| Field | Source |
|-------|--------|
| `organization_id` | `CurrentUser.organization_id` from auth |
| `created_by` | `CurrentUser.user_id` *(optional audit field)* |

---

# Flow 3 — Test connection (optional)

Runs when `test_connection: true`. If ping fails, return **400** with a clear message — do not save.

## Flow

```mermaid
flowchart TB
    VALID[Flow 2 passed]

    VALID --> CHECK{test_connection?}

    CHECK -->|false| F4[Skip — continue to Flow 4]
    CHECK -->|true| TYPE{type?}

    TYPE -->|mongo| M1[Motor / pymongo — ping admin]
    TYPE -->|http| H1[Resolve auth — OAuth2 token or static auth]
    H1 --> H2[GET base_url — timeout 5s]

    M1 --> OK{success?}
    H2 --> OK

    OK -->|yes| F4
    OK -->|no| E400[400 Connection test failed]
```

## Navigate to Flow 3 files

| Flow step | What happens | Open file |
|-----------|--------------|-----------|
| Ping orchestration | `ConnectorService.test_connection()` | [connector_service.py](../../app/services/connector_service.py) *(planned)* |
| Mongo ping | Connect + `ping` command | [mongo_connector_client.py](../../app/infrastructure/connectors/org/mongo_connector_client.py) *(planned)* |
| HTTP ping | Fetch OAuth2 token if needed, then `httpx` GET `base_url` | [connector_ping.py](../../app/services/connector_ping.py) |
| OAuth token | `fetch_oauth2_client_credentials_token()` | [http_token_provider.py](../../app/domain/executors/http_token_provider.py) |

## JSON at each step

| Step | Fields |
|------|--------|
| After Flow 2 | `name`, `type`, `config` validated |
| After ping success | `connection_tested: true` |
| After ping failure | error message, no Mongo insert |

---

# Flow 4 — Save to MongoDB

Insert connector document. Store secrets in `config` (encrypt at rest in a later phase; MVP may store as-is with restricted list/get masking).

## Flow

```mermaid
flowchart TB
    READY[Validated — optional ping passed]

    READY --> BUILD[Build connector document]

    subgraph DOC["Mongo document"]
        D1[_id — new ObjectId]
        D2[organization_id from CurrentUser]
        D3[name, description, type, config]
        D4[status = active]
        D5[created_at, updated_at]
        D1 --> D2 --> D3 --> D4 --> D5
    end

    BUILD --> DOC
    DOC --> INSERT[ConnectorRepository.insert]
    INSERT --> RES[201 — CreateConnectorResponse]
```

## Navigate to Flow 4 files

| Flow step | What happens | Open file |
|-----------|--------------|-----------|
| Service | `ConnectorService.create()` | [connector_service.py](../../app/services/connector_service.py) *(planned)* |
| Status constant | `CONNECTOR_STATUS_ACTIVE` | [connector_constants.py](../../app/domain/constants/connector_constants.py) *(planned)* |
| Save | Insert into `connectors` | [connector_repository.py](../../app/infrastructure/db/repositories/mongo/connector_repository.py) *(planned)* |
| Response schema | `CreateConnectorResponse` — mask secrets | [connector.py](../../app/schemas/connector.py) *(planned)* |

## MongoDB document shape

Collection: `connectors`

```json
{
  "_id": "6a3f8c12d8139334274fbbfe",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "name": "Customer MongoDB",
  "description": "Production customer database",
  "type": "mongo",
  "config": {
    "uri": "mongodb+srv://user:pass@cluster.example.net",
    "database": "customers"
  },
  "status": "active",
  "created_at": "2026-06-25T10:00:00Z",
  "updated_at": "2026-06-25T10:00:00Z"
}
```

## Response shape (`201`)

Secrets **masked** in API responses (e.g. `uri` → `mongodb+srv://***@cluster.example.net`, `auth_token` → `***`).

```json
{
  "id": "6a3f8c12d8139334274fbbfe",
  "name": "Customer MongoDB",
  "description": "Production customer database",
  "type": "mongo",
  "config": {
    "uri": "mongodb+srv://***@cluster.example.net",
    "database": "customers"
  },
  "status": "active",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "created_at": "2026-06-25T10:00:00Z",
  "updated_at": "2026-06-25T10:00:00Z"
}
```

## JSON at each step

| Step | Fields added |
|------|----------------|
| After auth | `organization_id` |
| After validation | `name`, `type`, `config` |
| After optional ping | `connection_tested: true` |
| After insert | `id`, `status`, `created_at`, `updated_at` |
| Final response | masked `config` + metadata |

## Example request

```http
POST /api/v1/connectors
Authorization: Bearer <clerk_jwt>
Content-Type: application/json

{
  "name": "ShoutOUT Loyalty API",
  "type": "http",
  "config": {
    "base_url": "https://api.loyalty.example.com",
    "auth_type": "oauth2_client_credentials",
    "token_url": "https://idp.loyalty.example.com/auth/realms/shoutout-loyalty-system/protocol/openid-connect/token",
    "client_id": "my-app-client",
    "client_secret": "..."
  },
  "test_connection": true
}
```

## Error responses

| Status | When |
|--------|------|
| `401` | Invalid or missing JWT |
| `422` | Invalid body or config for `type` |
| `409` | Connector `name` already exists in org |
| `400` | `test_connection: true` and ping failed |

---

# Relationship to Tools (next feature)

Tools reference connectors by id — org users do not repeat credentials in tool JSON:

```json
{
  "name": "customer_lookup",
  "executor": "mongo_find_one",
  "connector_id": "6a3f8c12d8139334274fbbfe",
  "config": {
    "collection": "customers",
    "filter": { "customer_id": "{{customer_id}}" }
  }
}
```

Executor `mongo_find_one` requires connector `type: mongo`. Validation happens at tool create time.
