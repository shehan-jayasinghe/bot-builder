# Preview Session Trace — `GET /api/v1/agents/{agent_id}/preview/sessions/{sender_id}/trace`

Returns the **Trace View** timeline (middle panel) for one preview session.

Trace is **saved on every chat turn** (preview and webhook). This GET is for **admin UI only** — end users never see it.

Related:

- Preview chat: [06-preview-chat-diagrams.md](./06-preview-chat-diagrams.md)
- Agent graph: [05-agent-runtime-graph-diagrams.md](./05-agent-runtime-graph-diagrams.md)
- Chat events: [01-chat-completion-diagrams.md](./01-chat-completion-diagrams.md) — Trace events table

**Agentic migration:** Phase A **Done** — no route/schema change. Phase B **Done** — `workflow_enter` trace no longer uses `reason: default_first_message`. Phase C **Done** — RAG stats on `tool_complete` for `search_knowledge`. Phase D **Done** — `sub_agent_continue` on sticky turns. See [../agentic/updets/api-migration-agentic-phase-d.md](../agentic/updets/api-migration-agentic-phase-d.md).

**LangChain proper (Done, no REST change):** Trace events on Mongo `TraceCollector`; LangSmith parent run per turn — [../agentic/updets/migration-langchain-proper.md](../agentic/updets/migration-langchain-proper.md).

**Status:** Implemented.

---

# Flow 1 — Auth

Same as [../agent/01-create-agent-diagrams.md](../agent/01-create-agent-diagrams.md) Flow 1.

```mermaid
flowchart TB
    REQ[GET /api/v1/agents/agent_id/preview/sessions/sender_id/trace]
    REQ --> API[API route]
    API --> DI[get_current_user]
    DI --> JWT[JWT verify]
    JWT -->|invalid| E401[401]
    JWT --> DB[user + org lookup]
    DB --> F2[Flow 2]
```

---

# Flow 2 — Load session trace

```mermaid
flowchart TB
    AUTH[CurrentUser — organization_id]
    AUTH --> PATH[agent_id + sender_id]

    PATH --> AGENT[AgentRepository — find by id + organization_id]
    AGENT -->|missing| E404A[404 Agent not found]

    AGENT --> TRK[TrackerRepository — find_by_session]
    TRK -->|missing| EMPTY[200 — empty turns]

    TRK --> DOC[Read trace[] + events from document]
    DOC --> RES[200 PreviewTraceResponse]
```

Session key: `(assistant_id = agent_id, sender_id)`.

---

# Example request

```http
GET /api/v1/agents/67agent001/preview/sessions/preview-session-9f2a/trace
Authorization: Bearer <clerk_jwt>
```

---

# Response `200`

```json
{
  "agent_id": "67agent001",
  "sender_id": "preview-session-9f2a",
  "source": "preview",
  "turns": [
    {
      "turn_id": "6a3f9012d8139334274ff01",
      "started_at": "2026-06-20T21:33:35.100Z",
      "events": [
        {
          "type": "input_message",
          "at": "2026-06-20T21:33:35.100Z",
          "data": { "message": "Hi" }
        },
        {
          "type": "guardrail_complete",
          "at": "2026-06-20T21:33:36.200Z",
          "data": {}
        },
        {
          "type": "rag_skipped",
          "at": "2026-06-20T21:33:36.200Z",
          "data": {}
        },
        {
          "type": "output_message",
          "at": "2026-06-20T21:33:37.000Z",
          "data": { "text": "Hello! How can I help you today?" }
        }
      ],
      "routing_decision": { "mode": "orchestrator" }
    },
    {
      "turn_id": "6a3f9012d8139334274ff02",
      "started_at": "2026-06-20T21:34:15.800Z",
      "events": [
        {
          "type": "input_message",
          "at": "2026-06-20T21:34:15.800Z",
          "data": { "message": "I want to know what are my top three spendings in Feb?" }
        },
        {
          "type": "guardrail_complete",
          "at": "2026-06-20T21:34:17.000Z",
          "data": {}
        },
        {
          "type": "tool_start",
          "at": "2026-06-20T21:34:17.500Z",
          "data": { "tool_name": "search_knowledge", "arguments": { "query": "top spendings February" } }
        },
        {
          "type": "tool_complete",
          "at": "2026-06-20T21:34:19.800Z",
          "data": {
            "tool_name": "search_knowledge",
            "kb_ids": ["6a3f9012d8139334274fbc01"],
            "chunk_count": 3,
            "context_length": 420
          }
        },
        {
          "type": "output_message",
          "at": "2026-06-20T21:34:20.200Z",
          "data": { "text": "Your top 3 spendings in February were:..." }
        }
      ],
      "routing_decision": {
        "mode": "orchestrator",
        "type": "tool",
        "name": "search_knowledge"
      }
    }
  ]
}
```

---

# Trace event types

| `type` | When | Trace UI label |
|--------|------|----------------|
| `input_message` | User message received | **Input Message** |
| `nemo_scripted_reply` | NeMo on; `scripted_intents.yml` match | **Output Message** — payload: `intent`, `matched_phrase` |
| `nemo_intent_blocked` | NeMo on; input rail refused | **LLM Request** → blocked — payload: `intent`, `rail` |
| `nemo_output_complete` | NeMo on; output self-check passed | **LLM Request** → `nemo_output_complete` |
| `nemo_output_blocked` | NeMo on; output rail blocked | **Output Message** — payload: `rail` |
| `guardrail_complete` | Policy check passed | **LLM Request** → `guardrail_complete` (payload: `gate: proceed` when NeMo on) |
| `bundle_loaded` | RuntimeBundle ready | *(optional — dev detail)* |
| `rag_skipped` | No KBs on agent or turn is in active workflow | **LLM Request** → `rag_skipped` |
| `tool_start` | Tool invoked (`search_knowledge` or executor) | **Tool Start** → tool name |
| `tool_complete` | Tool finished — for `search_knowledge` includes `kb_ids`, `chunk_count`, `context_length` | *(nested under tool)* |
| `sub_agent_start` | First delegate from orchestrator | *(feeds graph highlight)* |
| `sub_agent_continue` | Sticky follow-up on same sub-agent (Phase D **Done**) | *(feeds graph highlight)* |
| `sub_agent_complete` | Sub-agent turn finished | *(nested)* |
| `workflow_enter` / `workflow_step` / `slot_captured` / `workflow_exit` | Workflow runtime | *(feeds graph highlight)* |
| `output_message` | Assistant reply | **Output Message** |

Nested **LLM Request** rows in the UI = group `guardrail_complete` + `rag_skipped` (when applicable) under one turn step (same timestamp bucket). RAG retrieval stats appear on `tool_complete` when the LLM calls `search_knowledge`.

**Turn metadata** (stored on each turn, not a `type` in `events[]`): `routing_decision` — see below.

---

# `routing_decision` → graph highlight

| `routing_decision` | Highlight node |
|--------------------|----------------|
| `{ "mode": "orchestrator" }` | Center Agent node only |
| `{ "type": "tool", "name": "...", "tool_id": "..." }` | Tool node matching `tool_id` |
| `{ "type": "sub_agent", "sub_agent_id": "..." }` | Sub-agent node |
| `{ "type": "workflow", "workflow_id": "..." }` | Workflow node |

From [05-agent-runtime-graph-diagrams.md](./05-agent-runtime-graph-diagrams.md) `nodes[]`.

---

# Storage model (Mongo tracker document)

Trace stored **with** session — not a separate public API for webhook users:

```json
{
  "sender_id": "preview-session-9f2a",
  "assistant_id": "67agent001",
  "organization_id": "6a3b7c61d8139334274fbbfc",
  "source": "preview",
  "events": [],
  "turns": [
    {
      "turn_id": "...",
      "started_at": "...",
      "events": [],
      "routing_decision": {}
    }
  ],
  "active_agent_id": "67agent001",
  "active_agent_kind": "orchestrator",
  "last_routing_decision": {}
}
```

Webhook sessions use the same shape with `"source": "webhook"`. Admin GET trace is scoped to org + agent.

---

# Error responses

| Status | When |
|--------|------|
| `401` | Invalid JWT |
| `404` | Agent not found for org |
| `422` | Invalid `agent_id` format |
| `200` empty | No session yet — `{ "turns": [] }` |

---

# UI flow (all three panels)

```mermaid
sequenceDiagram
    participant UI as Preview UI
    participant Graph as GET runtime-graph
    participant Chat as POST preview/chat
    participant Trace as GET trace

    UI->>Graph: On page load
    Graph-->>UI: nodes + edges

    UI->>Chat: User sends message
    Chat-->>UI: messages[]

    UI->>Trace: Poll after chat
    Trace-->>UI: turns + routing_decision
    UI->>UI: Render timeline + highlight graph node
```

---

# Navigate to implementation files

| What | Open file |
|------|-----------|
| Route | [agents.py](../../app/api/v1/agents.py) |
| Schema | [preview.py](../../app/schemas/preview.py) |
| Service | [preview_trace_service.py](../../app/services/preview_trace_service.py) |
| DI | [preview.py](../../app/di/preview.py) |
| Record events | [trace.py](../../app/domain/pipeline/observability/trace.py) |
| Session store | [tracker.py](../../app/domain/models/tracker.py) · [tracker_service.py](../../app/services/tracker_service.py) |
