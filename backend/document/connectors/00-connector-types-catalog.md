# Connector Types Catalog — `GET /api/v1/connector-types`

Read-only catalog for the UI: which org connector types exist, labels, and required `config` fields per type.

No secrets. No org scoping — same list for all authenticated users. Optional: allow unauthenticated read for public docs; MVP uses same auth as other routes.

**Agentic migration:** **No** API change. See [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md).

**Not included:** platform connectors (Bedrock, S3, app Mongo, Qdrant for KB) — those are not org connections.

---

# All org connector types (7)

| # | `type` | Label | MVP | Used by executors (tools) |
|---|--------|-------|-----|---------------------------|
| 1 | `mongo` | MongoDB | yes | `mongo_find_one`, `mongo_find_many`, `mongo_insert`, `mongo_update`, `mongo_delete`, `mongo_aggregate` |
| 2 | `http` | REST / HTTP | yes | `http_request` |
| 3 | `sql` | SQL | phase 2 | `sql_select`, `sql_insert`, `sql_update`, `sql_delete` |
| 4 | `graphql` | GraphQL | phase 2 | `graphql_query`, `graphql_mutation` |
| 5 | `grpc` | gRPC | phase 2 | `grpc_call` |
| 6 | `redis` | Redis | phase 2 | `redis_get`, `redis_set`, `redis_delete` |
| 7 | `vector` | Vector DB | phase 2 | `vector_search`, `vector_upsert`, `vector_delete` |

---

# Config schema per type

## `mongo`

```json
{
  "uri": "mongodb+srv://user:pass@host",
  "database": "my_db"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `uri` | yes | Full MongoDB connection string |
| `database` | yes | Default database name for tools |

---

## `http`

**OAuth2 client credentials (recommended for production REST APIs — Keycloak, Auth0, etc.)**

```json
{
  "base_url": "https://api.loyalty.example.com",
  "auth_type": "oauth2_client_credentials",
  "token_url": "https://idp.example.com/auth/realms/app/protocol/openid-connect/token",
  "client_id": "my-app-client",
  "client_secret": "...",
  "grant_type": "client_credentials",
  "scope": "read write",
  "default_headers": {
    "Accept": "application/json"
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `base_url` | yes | Target REST API — no trailing slash; tool config adds path |
| `auth_type` | no | `none`, `oauth2_client_credentials`, `api_key`, `basic`, `bearer` — default `none` |
| `token_url` | when oauth2 | OAuth token endpoint (separate from `base_url`) |
| `client_id` | when oauth2 | App / client identifier |
| `client_secret` | when oauth2 | Secret — masked in API responses; platform fetches and refreshes access tokens |
| `grant_type` | when oauth2 | Default `client_credentials` |
| `scope` | no | Optional OAuth scope string |
| `auth_token` | when api_key / bearer | Secret — masked; `bearer` is dev-only static token |
| `auth_username` | when basic | |
| `auth_password` | when basic | Secret |
| `api_key_header` | when api_key | e.g. `X-API-Key` |
| `default_headers` | no | Merged into every tool HTTP call |

**Static bearer (dev / internal APIs only)**

```json
{
  "base_url": "https://api.example.com",
  "auth_type": "bearer",
  "auth_token": "sk_live_..."
}
```

Platform behavior for `oauth2_client_credentials`:

1. `POST token_url` with `client_id`, `client_secret`, `grant_type=client_credentials`
2. Cache `access_token` until near expiry
3. Attach `Authorization: Bearer <access_token>` on every `http_request` tool call

---

## `sql` (phase 2)

```json
{
  "dialect": "postgresql",
  "host": "db.example.com",
  "port": 5432,
  "database": "analytics",
  "username": "app_user",
  "password": "secret"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `dialect` | yes | `postgresql`, `mysql` |
| `host` | yes | |
| `port` | yes | |
| `database` | yes | |
| `username` | yes | |
| `password` | yes | Secret |

---

## `graphql` (phase 2)

```json
{
  "endpoint": "https://api.example.com/graphql",
  "headers": {
    "Authorization": "Bearer ..."
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `endpoint` | yes | GraphQL HTTP endpoint |
| `headers` | no | Auth headers — secrets masked |

---

## `grpc` (phase 2)

```json
{
  "host": "grpc.example.com",
  "port": 50051,
  "tls": true,
  "metadata": {}
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `host` | yes | |
| `port` | yes | |
| `tls` | no | default `true` |
| `metadata` | no | Per-call metadata defaults |

---

## `redis` (phase 2)

```json
{
  "url": "redis://:password@host:6379/0"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `url` | yes | Redis connection URL — secret masked |

---

## `vector` (phase 2)

```json
{
  "provider": "qdrant",
  "url": "https://xyz.qdrant.io",
  "api_key": "..."
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `provider` | yes | `qdrant`, `pinecone`, … |
| `url` | yes | |
| `api_key` | optional | Secret — masked |

---

# API response shape — `GET /api/v1/connector-types`

```json
{
  "items": [
    {
      "type": "mongo",
      "label": "MongoDB",
      "description": "Connect to a MongoDB database for read/write tools.",
      "mvp": true,
      "config_schema": {
        "uri": { "type": "string", "required": true, "secret": true },
        "database": { "type": "string", "required": true, "secret": false }
      },
      "compatible_executors": [
        "mongo_find_one",
        "mongo_find_many",
        "mongo_insert",
        "mongo_update",
        "mongo_delete",
        "mongo_aggregate"
      ]
    },
    {
      "type": "http",
      "label": "REST / HTTP",
      "description": "Connect to a REST API with optional authentication.",
      "mvp": true,
      "config_schema": {
        "base_url": { "type": "string", "required": true, "secret": false },
        "auth_type": {
          "type": "enum",
          "values": ["none", "oauth2_client_credentials", "api_key", "basic", "bearer"],
          "required": false
        },
        "token_url": { "type": "string", "required": false, "secret": false },
        "client_id": { "type": "string", "required": false, "secret": false },
        "client_secret": { "type": "string", "required": false, "secret": true },
        "grant_type": { "type": "string", "required": false, "secret": false },
        "scope": { "type": "string", "required": false, "secret": false },
        "auth_token": { "type": "string", "required": false, "secret": true }
      },
      "compatible_executors": ["http_request"]
    }
  ]
}
```

---

# Executor ↔ connector type matching

When creating a **Tool**, validate that `connector.type` matches the executor family:

| Executor prefix / name | Required connector `type` |
|------------------------|---------------------------|
| `mongo_*` | `mongo` |
| `http_request` | `http` |
| `sql_*` | `sql` |
| `graphql_*` | `graphql` |
| `grpc_call` | `grpc` |
| `redis_*` | `redis` |
| `vector_*` | `vector` |

---

# Navigate to implementation files

| What | Open file |
|------|-----------|
| API route | [connectors.py](../../app/api/v1/connectors.py) |
| Type enum | [connector_constants.py](../../app/domain/constants/connector_constants.py) |
| Static catalog | [connector_type_catalog.py](../../app/domain/catalog/connector_type_catalog.py) |
| OAuth token fetch | [http_token_provider.py](../../app/domain/executors/http_token_provider.py) |
| HTTP executor auth | [http_ops.py](../../app/domain/executors/http_ops.py) |
