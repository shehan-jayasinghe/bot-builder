# Chat Completion — `POST /api/v1/chat/webhook/{webhook_id}`

Main inference endpoint for the **web widget** and channels. End user sends a message; platform returns assistant reply/replies.

**Not org JWT auth (MVP).** `webhook_id` identifies the channel. Service token — phase 2.

Capabilities (no separate Skills layer): **orchestrator agent**, **sub-agents**, **tools**, **knowledge bases**, **workflows**.

**Agentic migration (capability catalog):** [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md) — this endpoint has **no REST/schema change**; runtime builds final prompt from `system_prompt` + guardrails + catalog + optional RAG.

Related config docs:

- Agent: [../agent/01-create-agent-diagrams.md](../agent/01-create-agent-diagrams.md) · [../agent/03-list-agents-diagrams.md](../agent/03-list-agents-diagrams.md)
- Tools: [../tools/00-executor-catalog.md](../tools/00-executor-catalog.md) · runtime: [../tools/03-execute-tool-at-chat-diagrams.md](../tools/03-execute-tool-at-chat-diagrams.md)
- Knowledge bases: [../knowledgebase/01-create-knowledgebase-diagrams.md](../knowledgebase/01-create-knowledgebase-diagrams.md)
- Workflows: [../workflows/01-create-workflow-diagrams.md](../workflows/01-create-workflow-diagrams.md)
- Sub-agents: [../sub-agents/01-create-sub-agent-diagrams.md](../sub-agents/01-create-sub-agent-diagrams.md)

**Next-pass specs:**

- Agentic catalog + prompt layers — [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md)
- Phase 2 — [02-sub-agent-delegation-at-chat-diagrams.md](./02-sub-agent-delegation-at-chat-diagrams.md)
- Phase 3 — [03-rag-at-chat-diagrams.md](./03-rag-at-chat-diagrams.md) (agentic `search_knowledge` tool — Phase C in migration doc)
- Phase 4 — [04-workflow-runtime-at-chat-diagrams.md](./04-workflow-runtime-at-chat-diagrams.md)

**Preview UI (admin builder — planned):**

- [05-agent-runtime-graph-diagrams.md](./05-agent-runtime-graph-diagrams.md) — `GET .../runtime-graph`
- [06-preview-chat-diagrams.md](./06-preview-chat-diagrams.md) — `POST .../preview/chat`
- [07-preview-session-trace-diagrams.md](./07-preview-session-trace-diagrams.md) — `GET .../preview/sessions/{sender_id}/trace`

---

# Implementation status

| Phase | Flows | Status | What runs today |
|-------|--------|--------|-----------------|
| **0** | 1–5, 12 | **Done** | Request validation, channel/agent resolve (friendly 200 fallback), tracker, RuntimeBundle batch hydrate, PII redaction, guardrails, orchestrator LLM, persist + response |
| **1** | 6–7, 10 | **Done** | Orchestrator Bedrock turn with tool calling via `ExecutorRegistry` + `langgraph_tools` |
| **2** | 8 | **Done** | Sub-agent delegation at runtime — see [02-sub-agent-delegation-at-chat-diagrams.md](./02-sub-agent-delegation-at-chat-diagrams.md) |
| **3** | 9 | **Done** (always-on RAG) · **Next** (agentic RAG tool) | Qdrant / keyword RAG — see [03-rag-at-chat-diagrams.md](./03-rag-at-chat-diagrams.md) |
| **4** | 11 | **Done** | Workflow runtime — see [04-workflow-runtime-at-chat-diagrams.md](./04-workflow-runtime-at-chat-diagrams.md) |
| **A** | — | **Next** | Capability catalog + `FinalPromptBuilder` — [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md) |

**Current runtime path:** `chat.py` → `ChatCompletionService` → sanitize → guardrails → `RuntimeBundleLoader` → `ChatGraph` → orchestrator / workflow → `TrackerService.persist`.

---

# High-level flow

```mermaid
flowchart TB
    USER[User message]
    API[POST /api/v1/chat/webhook/webhook_id]
    SVC[ChatCompletionService.complete]

    USER --> API --> SVC

    SVC --> F2[Flow 2 — channel + agent]
    F2 --> F3[Flow 3 — tracker]
    F3 --> F4[Flow 4 — RuntimeBundle]
    F4 --> F5[Flow 5 — sanitize + guardrails]
    F5 --> F6[Flow 6 — ChatGraph routing]
    F6 --> F7[Flow 7 — orchestrator + tools]
    F6 --> F8[Flow 8 — sub-agent]
    F6 --> F9[Flow 9 — RAG]
    F6 --> F11[Flow 11 — workflow]
    F7 --> F12[Flow 12 — persist + response]
    F8 --> F12
    F11 --> F12
```

---

# Flow 1 — Validate request

```mermaid
flowchart TB
    REQ[POST /api/v1/chat/webhook/webhook_id]
    REQ --> BODY[Pydantic — ChatRequest]
    BODY -->|invalid| E422[422]
    BODY --> F2[Flow 2]
```

### Request body

```json
{
  "sender_id": "user-abc-123",
  "message": "What is my loyalty balance?",
  "metadata": {
    "page_url": "https://example.com/help"
  }
}
```

| Field | Rule |
|-------|------|
| `sender_id` | required — stable per end user in channel |
| `message` | required, min length 1 |
| `metadata` | optional object |

---

# Flow 2 — Resolve channel + orchestrator agent

```mermaid
flowchart TB
    PATH[webhook_id path param]
    PATH --> CH[ChannelRepository — find_active_by_webhook_id]
    CH -->|missing| FALL[200 — friendly unavailable message]
    CH -->|no agent_id| FALL
    CH --> AG[AgentRepository — find_published_by_id]
    AG -->|missing / draft| FALL
    AG --> F3[Flow 3]
```

Orchestrator = **published** parent agent linked to channel.

### Friendly fallback `200` (not 500)

```json
{
  "messages": [
    {
      "recipient_id": "user-abc-123",
      "text": "This assistant is temporarily unavailable. Please contact support.",
      "buttons": null
    }
  ]
}
```

---

# Flow 3 — Load session (tracker)

```mermaid
flowchart TB
    AGENT[Orchestrator agent loaded]
    AGENT --> TRK[TrackerService.load_or_create]
    TRK --> REDIS[Redis session — hot]
    TRK --> MONGO[Mongo — cold]
    TRK --> APPEND[append_user_message — sanitized in Flow 5]
    APPEND --> F4[Flow 4]
```

### Tracker fields (existing + planned)

```json
{
  "sender_id": "user-abc-123",
  "assistant_id": "67agent001",
  "events": [
    { "role": "user", "content": "...", "timestamp": "..." },
    { "role": "assistant", "content": "...", "timestamp": "..." }
  ],
  "active_agent_id": "67agent001",
  "active_agent_kind": "orchestrator",
  "active_flow_state": null,
  "last_routing_decision": null
}
```

| Field | Purpose |
|-------|---------|
| `events` | LLM history (cap last N turns) |
| `active_flow_state` | Workflow position + slots — Flow 11 |
| `active_agent_kind` | `orchestrator` \| `sub_agent` \| `workflow` |

---

# Flow 4 — RuntimeBundle loader (batch hydrate)

Mongo stores **IDs only** on agent / sub-agent. Chat hydrates once per turn (or Redis cache).

```mermaid
flowchart TB
    AGENT[Published agent — tool_ids, knowledge_base_ids, workflow_ids, sub_agent_ids]
    AGENT --> P1[tools find _id in tool_ids]
    AGENT --> P2[knowledgebases find _id in kb_ids]
    AGENT --> P3[workflows find _id in workflow_ids]
    AGENT --> P4[sub_agents find _id in sub_agent_ids]
    P1 --> MERGE[RuntimeBundle]
    P2 --> MERGE
    P3 --> MERGE
    P4 --> SUB[Batch hydrate each sub-agent tool/kb/workflow ids]
    SUB --> MERGE
    MERGE --> FILTER[active tools, ready KBs, active sub-agents]
    FILTER --> F5[Flow 5]
```

**~6–9 batch queries** — not one call per ID. See [../tools/03-execute-tool-at-chat-diagrams.md](../tools/03-execute-tool-at-chat-diagrams.md).

### RuntimeBundle shape (in-memory)

```json
{
  "orchestrator": {
    "id": "67agent001",
    "name": "Support Bot",
    "system_prompt": "...",
    "tools": [{ "id": "...", "name": "customer_lookup", "description": "...", "executor": "mongo_find_one", "config": {} }],
    "knowledge_bases": [{ "id": "...", "name": "Policy docs", "storage_type": "vector", "status": "ready" }],
    "workflows": [{ "id": "...", "name": "Onboarding", "nodes": [], "edges": [] }],
    "sub_agents": [{
      "id": "...",
      "name": "research_agent",
      "description": "...",
      "instructions": "...",
      "parameters": [],
      "tools": [],
      "knowledge_bases": [],
      "workflows": []
    }]
  },
  "organization_id": "6a3b7c61d8139334274fbbfc"
}
```

---

# Flow 5 — Sanitize message + guardrails

```mermaid
flowchart TB
    RAW[Raw user message]
    RAW --> REDACT[PII redaction — email, phone, secrets]
    REDACT --> GUARD[GuardrailRunner — agent guardrails]
    GUARD -->|block| REFUSE[Safe refusal reply]
    GUARD -->|ok| CLEAN[Sanitized text → tracker + graph]
    CLEAN --> F6[Flow 6]
```

- **Redact** before LLM and tracker storage — do not hash for model input.
- Slot extractor **not** used here — only Flow 11 (workflow `input` nodes).

---

# Flow 6 — LangGraph routing

**Status: done.** Implemented in [chat_graph.py](../../app/domain/graph/chat_graph.py) and wired from [chat_completion_service.py](../../app/services/chat_completion_service.py).

```mermaid
flowchart TB
    START[chat_turn]
    START --> MODE{active_flow_state set?}
    MODE -->|yes| F11[Flow 11 — workflow]
    MODE -->|no| F7[Flow 7 — orchestrator]
    F11 -->|done| F7
    F7 -->|delegate| F8[Flow 8 — sub-agent]
    F7 -->|tool| F10[Flow 10 — tool]
    F7 -->|KB attached| F9[Flow 9 — RAG]
    F8 -->|tool| F10
    F9 --> F7
    F10 --> F7
    F7 --> F12[Flow 12]
    F8 --> F12
    F11 --> F12
```

---

# Flow 7 — Orchestrator node

**Status: done** (simple path — no sub-agent delegate functions yet).

```mermaid
flowchart TB
    BUNDLE[RuntimeBundle.orchestrator]
    BUNDLE --> PROMPT[system_prompt + personality + tone + RAG context]
    BUNDLE --> TOOLS[LLM tool defs from bundle.tools]
    BUNDLE --> SUBS[Delegate functions from bundle.sub_agents]
    PROMPT --> LLM[Bedrock converse + tool use]
    TOOLS --> LLM
    SUBS --> LLM
    LLM --> HIST[tracker history + user_message]
    LLM --> OUT{text | tool_use | delegate}
```

Sub-agent function example:

```json
{
  "name": "research_agent",
  "description": "Deep research tasks",
  "parameters": { "type": "object", "properties": { "query": { "type": "string" } }, "required": ["query"] }
}
```

---

# Flow 8 — Sub-agent delegation

**Status: done** — delegate tools via `SubAgentRunner`. Spec: [02-sub-agent-delegation-at-chat-diagrams.md](./02-sub-agent-delegation-at-chat-diagrams.md).

**Agentic next (runtime):** sticky handover — [../agentic/updets/runtime-migration-agentic.md](../agentic/updets/runtime-migration-agentic.md).

```mermaid
flowchart TB
    ORCH[Orchestrator calls research_agent]
    ORCH --> SET[tracker.active_agent_id = sub_agent.id]
    SET --> PROMPT[system = sub_agent.instructions + delegate params]
    PROMPT --> SCOPE[Scoped tools + KBs from sub_agent in bundle]
    SCOPE --> LLM[Bedrock]
    LLM -->|tool| F10[Flow 10]
    LLM -->|text| F12[Flow 12]
```

MVP: reset to orchestrator on **next** user message unless workflow active.

---

# Flow 9 — RAG retrieval (knowledge bases)

**Status: done** (always-on) — `RAGRetriever` before orchestrator; skipped during active workflow. Spec: [03-rag-at-chat-diagrams.md](./03-rag-at-chat-diagrams.md).

**Agentic Phase C (runtime):** replace always-on RAG with `search_knowledge` LLM tool — [../agentic/updets/runtime-migration-agentic.md](../agentic/updets/runtime-migration-agentic.md).

```mermaid
flowchart TB
    SCOPE[Active agent KB list from bundle]
    SCOPE --> FILTER[status == ready]
    FILTER --> TYPE{storage_type}
    TYPE -->|vector| Q[Qdrant similarity]
    TYPE -->|keyword| T[TF-IDF search]
    TYPE -->|graph| G[Neo4j — phase 2]
    Q --> CTX[rag_context injected into prompt]
    T --> CTX
```

Ingest: [LlamaIndexPipeline](../../app/infrastructure/ai/indexers/llama_index_pipeline.py). Query: [RAGRetriever](../../app/domain/pipeline/rag/retriever.py).

Scope: orchestrator KBs or sub-agent KBs depending on `active_agent_kind`.

---

# Flow 10 — Tool execution

**Status: done** when orchestrator has active tools in the bundle.

```mermaid
flowchart TB
    LLM[orchestrator or sub_agent — tool_use]
    LLM --> RESOLVE[Tool from active scope in bundle]
    RESOLVE --> CONN[Connector — org scoped]
    CONN --> EXEC[ExecutorRegistry.run]
    EXEC --> TRACE[tool_start / tool_complete]
    TRACE --> LLM2[Return result to same LLM node]
```

Full detail: [../tools/03-execute-tool-at-chat-diagrams.md](../tools/03-execute-tool-at-chat-diagrams.md).

---

# Flow 11 — Workflow runtime + slot capture

**Status: done** — `workflow_runner` + `ChatGraph` routing. Spec: [04-workflow-runtime-at-chat-diagrams.md](./04-workflow-runtime-at-chat-diagrams.md).

**Agentic next (runtime):** remove `default_first_message` rule — LLM picks workflow from catalog. See [../agentic/updets/runtime-migration-agentic.md](../agentic/updets/runtime-migration-agentic.md).

Only when `tracker.active_flow_state` is set.

```mermaid
flowchart TB
    WF[workflow_node — current_node_id]
    WF --> TYPE{node type?}
    TYPE -->|start| NEXT[Follow edge]
    TYPE -->|message| OUT[Emit data.text — {{slot}} substitute]
    TYPE -->|input| SLOT[Capture user message into slots]
    TYPE -->|output| REPLY[User reply]
    TYPE -->|end| CLEAR[Clear flow state]

    SLOT --> VAL{valid?}
    VAL -->|no| RETRY[Ask again]
    VAL -->|yes| NEXT
```

### `input` node slot capture (workflow-only — not global SlotExtractor)

```json
{
  "active_flow_state": {
    "workflow_id": "6a3f9012d8139334274fbc00",
    "current_node_id": "input-1",
    "slots": { "customer_id": "123456" },
    "awaiting_slot": null
  }
}
```

Normal orchestrator / sub-agent / tool chat does **not** use slot extractor.

---

# Flow 12 — Persist + response

```mermaid
flowchart TB
    REPLIES[Assistant reply text]
    REPLIES --> TRK[tracker.append_assistant_replies]
    TRK --> STATE[Save routing + active_flow_state]
    STATE --> REDIS[Redis set]
    STATE --> MONGO[Mongo persist]
    MONGO --> TRACE[TraceCollector — routing_decision, output_message]
    TRACE --> RES[200 ChatResponse]
```

### Response `200`

```json
{
  "messages": [
    {
      "recipient_id": "user-abc-123",
      "text": "Your loyalty balance is 1,250 points.",
      "buttons": null
    }
  ]
}
```

---

# Trace events (per turn)

| Event | When |
|-------|------|
| `input_message` | Turn start |
| `guardrail_complete` / `guardrail_blocked` | Flow 5 |
| `bundle_loaded` | Flow 4 |
| `routing_decision` | Agent/workflow switch |
| `rag_complete` | Flow 9 |
| `tool_start` / `tool_complete` / `tool_error` | Flow 10 |
| `workflow_step` / `slot_captured` | Flow 11 |
| `output_message` | Flow 12 |

---

# Error responses

| Status | When |
|--------|------|
| `422` | Invalid body |
| `200` | Channel/agent missing — fallback text |
| `429` | Rate limit — phase 2 |
| `500` | Unexpected — generic user message |

---

# Example request

```http
POST /api/v1/chat/webhook/wh_abc123xyz
Content-Type: application/json

{
  "sender_id": "sess-9f2a",
  "message": "I need help with my account",
  "metadata": {}
}
```

---

# Legacy migration

| Removed | Replaced with |
|---------|----------------|
| `skill_ids` on agent (write path) | `tool_ids` — legacy `skill_ids` read at load time when `tool_ids` is empty |

---

# Agentic migration — API impact on this endpoint

| Item | Change |
|------|--------|
| `POST /api/v1/chat/webhook/{webhook_id}` route | **No** |
| `ChatRequest` / `ChatResponse` schemas | **No** |
| Runtime | **Yes** — `FinalPromptBuilder` assembles `[1] system_prompt` + `[2] guardrails` + `[3] capability_catalog` + `[4] rag_context` (Phase C only) |

Full API matrix: [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md)

---

# Implementation phases

| Phase | Flows | Status | Doc |
|-------|--------|--------|-----|
| 0 | 1–5, 12 | Done | this file |
| 1 | 6–7, 10 | Done | this file · [tools/03-execute-tool-at-chat-diagrams.md](../tools/03-execute-tool-at-chat-diagrams.md) |
| 2 | 8 | Done | [02-sub-agent-delegation-at-chat-diagrams.md](./02-sub-agent-delegation-at-chat-diagrams.md) |
| 3 | 9 | Done | [03-rag-at-chat-diagrams.md](./03-rag-at-chat-diagrams.md) |
| 4 | 11 | Done | [04-workflow-runtime-at-chat-diagrams.md](./04-workflow-runtime-at-chat-diagrams.md) |
| A | catalog | Next | [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md) |

---

# Navigate to implementation files

| What | Open file | Status |
|------|-----------|--------|
| API route | [chat.py](../../app/api/v1/chat.py) | Done |
| Entry service | [chat_completion_service.py](../../app/services/chat_completion_service.py) | Done |
| Schemas | [schemas/chat.py](../../app/schemas/chat.py) | Done |
| Graph routing | [chat_graph.py](../../app/domain/graph/chat_graph.py) | Done |
| Runtime bundle | [runtime_bundle.py](../../app/domain/models/runtime_bundle.py) · [runtime_bundle_loader.py](../../app/services/runtime_bundle_loader.py) | Done |
| Orchestrator | [orchestrator.py](../../app/domain/graph/orchestrator.py) | Done |
| Sub-agent delegate | [sub_agent_delegate.py](../../app/domain/graph/sub_agent_delegate.py) | Done |
| Workflow runtime | [workflow_runner.py](../../app/domain/workflow/workflow_runner.py) | Done |
| Assistant resolve | [assistant_loader.py](../../app/services/assistant_loader.py) | Done |
| Tracker | [tracker.py](../../app/domain/models/tracker.py) · [tracker_service.py](../../app/services/tracker_service.py) | Done |
| LLM | [llm.py](../../app/infrastructure/ai/llm.py) | Done |
| PII sanitizer | [pii_redactor.py](../../app/domain/pipeline/sanitization/pii_redactor.py) | Done |
| Guardrails | [guardrails/runner.py](../../app/domain/pipeline/guardrails/runner.py) | Done |
| Tool execution | [langgraph_tools.py](../../app/domain/executors/langgraph_tools.py) · [registry.py](../../app/domain/executors/registry.py) | Done |
| RAG query | [retriever.py](../../app/domain/pipeline/rag/retriever.py) | Done |
| Trace | [trace.py](../../app/domain/pipeline/observability/trace.py) | Done |
| DI | [di/chat.py](../../app/di/chat.py) | Done |
