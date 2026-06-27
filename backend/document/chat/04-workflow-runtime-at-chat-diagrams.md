# Workflow Runtime at Chat — Phase 4

**Not a new REST endpoint.** Runs inside `POST /api/v1/chat/webhook/{webhook_id}` when `tracker.active_flow_state` is set.

Parent doc: [01-chat-completion-diagrams.md](./01-chat-completion-diagrams.md) · Flow 11

Workflow REST: [../workflows/01-create-workflow-diagrams.md](../workflows/01-create-workflow-diagrams.md) · model: [../workflows/00-workflow-model.md](../workflows/00-workflow-model.md)

**Prerequisite:** Phase 0 + 1 done. Workflows attached to agent with `status: published`.

**Status:** Implemented — `workflow_runner` + `ChatGraph` routing.

**Agentic migration (REST):** Phase A **Done** — [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md). Phase B **Done** (runtime) — [../agentic/updets/api-migration-agentic-phase-b.md](../agentic/updets/api-migration-agentic-phase-b.md) · [../agentic/updets/runtime-migration-agentic-phase-b.md](../agentic/updets/runtime-migration-agentic-phase-b.md). Phase C **no REST change**. Phase D **planned** — active workflow takes priority over sticky sub-agent (no REST change). See [../agentic/updets/api-migration-agentic-phase-d.md](../agentic/updets/api-migration-agentic-phase-d.md).

---

# Goal

Execute the workflow graph **step by step** inside chat:

- **`message` nodes** — emit text (with `{{slot}}` substitution)
- **`input` nodes** — capture the user's message into named slots (workflow-only — **not** global `SlotExtractor`)
- **`output` nodes** — treat as user-facing reply
- **`end` nodes** — clear `active_flow_state`, return to orchestrator (Flow 7)

Workflow takes **priority** over orchestrator when `active_flow_state` is non-null.

---

# High-level flow

```mermaid
flowchart TB
    TURN[Chat turn]
    TURN --> CHECK{tracker.active_flow_state?}
    CHECK -->|no| F7[Flow 7 — orchestrator]
    CHECK -->|yes| F11[Flow 11 — workflow]

    F11 --> NODE[Load current node from workflow JSON]
    NODE --> TYPE{node.type}

    TYPE -->|start| NEXT[Follow edge to next node]
    TYPE -->|message| EMIT[Emit data.text — substitute slots]
    TYPE -->|input| SLOT[Capture user message into slot]
    TYPE -->|output| REPLY[Assistant reply]
    TYPE -->|end| CLEAR[Clear active_flow_state]

    SLOT --> VAL{valid?}
    VAL -->|no| RETRY[Ask again — stay on input node]
    VAL -->|yes| NEXT

    NEXT --> PERSIST[Update active_flow_state]
    EMIT --> PERSIST
    REPLY --> PERSIST
    CLEAR --> F7
    PERSIST --> F12[Flow 12 — persist + response]
```

---

# Flow 1 — Enter workflow

Workflow starts when:

1. **Orchestrator LLM** calls a `workflow_<name>` delegate tool (`enter_reason: orchestrator_tool`) — **primary path after Phase B**
2. User is already in a workflow (`active_flow_state` → `enter_reason: active_state`)

**Phase B (Done):** removed hardcoded auto-start on first message (`default_first_message`). Workflows enter via LLM `workflow_*` tool or `active_flow_state`. Spec: [../agentic/updets/runtime-migration-agentic-phase-b.md](../agentic/updets/runtime-migration-agentic-phase-b.md).

~~2. Channel / agent config triggers a default workflow on first message (optional MVP+)~~ — **removed in Phase B**

```mermaid
flowchart TB
    START[Enter workflow]
    START --> WF[Resolve RuntimeWorkflow from bundle by id]
    WF --> NODE[Find start node — type start]
    NODE --> EDGE[Follow first outgoing edge]
    EDGE --> SET[active_flow_state = workflow_id + current_node_id + slots]
```

### Initial `active_flow_state`

```json
{
  "workflow_id": "6a3f9012d8139334274fbc00",
  "current_node_id": "message-1",
  "slots": {},
  "awaiting_slot": null
}
```

---

# Flow 2 — `message` node

```mermaid
flowchart TB
    NODE[message node — data.text]
    NODE --> SUB[Substitute {{slot_name}} from slots map]
    SUB --> OUT[Append to assistant replies]
    OUT --> NEXT[Advance to next node via edge]
```

Example node:

```json
{
  "id": "message-1",
  "type": "message",
  "data": { "text": "Hello {{customer_name}}, how can I help?" }
}
```

---

# Flow 3 — `input` node (slot capture)

**Only place slot capture runs in chat** — not in Flow 5 sanitize.

```mermaid
flowchart TB
    NODE[input node — data.slot_name + validation]
    NODE --> AWAIT{awaiting_slot set?}
    AWAIT -->|no| PROMPT[Emit data.prompt — ask user]
    AWAIT -->|yes| CAPTURE[Use user message as slot value]
    CAPTURE --> VAL{Validate type / regex / required}
    VAL -->|fail| RETRY[Emit data.retry_message]
    VAL -->|ok| STORE[slots.slot_name = value]
    STORE --> NEXT[Advance node — clear awaiting_slot]
```

### `input` node example

```json
{
  "id": "input-1",
  "type": "input",
  "data": {
    "slot_name": "customer_id",
    "prompt": "Please enter your customer ID.",
    "retry_message": "That doesn't look valid. Try again.",
    "validation": { "type": "string", "pattern": "^[0-9]{6,12}$" }
  }
}
```

### State while waiting

```json
{
  "workflow_id": "6a3f9012d8139334274fbc00",
  "current_node_id": "input-1",
  "slots": {},
  "awaiting_slot": "customer_id"
}
```

After valid capture:

```json
{
  "workflow_id": "6a3f9012d8139334274fbc00",
  "current_node_id": "message-2",
  "slots": { "customer_id": "123456" },
  "awaiting_slot": null
}
```

---

# Flow 4 — `output` and `end` nodes

| Node type | Behavior |
|-----------|----------|
| `output` | Emit `data.text` as assistant reply; may chain to next node in same turn or wait for next message |
| `end` | Set `active_flow_state = null`; optionally emit farewell `data.text` |

```mermaid
flowchart TB
    END[end node]
    END --> CLEAR[tracker.set_active_flow_state null]
    CLEAR --> KIND[tracker.active_agent_kind = orchestrator]
    KIND --> F7[Next turn — orchestrator]
```

---

# Flow 5 — Integration with LangGraph routing (Flow 6)

**Status: done** — `ChatGraph` routes workflow vs orchestrator; orchestrator can enter workflow via `workflow_*` tool (Phase B).

```mermaid
flowchart TB
    START[chat_turn]
    START --> MODE{active_flow_state set?}
    MODE -->|yes| F11[Flow 11]
    MODE -->|no| F7[Flow 7]
    F7 -->|workflow_* tool| F11
    F11 -->|exited| F7
```

`ChatCompletionService` delegates to `ChatGraph.run_turn` (not direct `OrchestratorRunner`).

---

# Trace events

| Event | When |
|-------|------|
| `workflow_step` | Node processed — `node_id`, `type` |
| `slot_captured` | Valid input stored — `slot_name` (not raw PII in logs) |
| `workflow_enter` | Workflow started |
| `workflow_exit` | `end` node — state cleared |
| `routing_decision` | `type: workflow` |

---

# Implementation files (done)

| File | Role |
|------|------|
| [workflow_runner.py](../../app/domain/workflow/workflow_runner.py) | Node dispatch + slot validation |
| [slot_validator.py](../../app/domain/workflow/slot_validator.py) | Regex / type checks for `input` nodes |
| [chat_graph.py](../../app/domain/graph/chat_graph.py) | Flow 6 router — workflow vs orchestrator; LLM `workflow_*` entry (Phase B) |
| [chat_completion_service.py](../../app/services/chat_completion_service.py) | Wires `ChatGraph`; RAG skip when `in_workflow` only |
| [tracker.py](../../app/domain/models/tracker.py) | Flow state transitions |
| [workflow_delegate.py](../../app/domain/workflow/workflow_delegate.py) | `workflow_*` LangGraph tools + `routing_hint` in descriptions |
| Tests | [test_workflow_runtime_at_chat.py](../../tests/test_workflow_runtime_at_chat.py) |

**No API schema change** — same `ChatRequest` / `ChatResponse`. Optional future: `metadata.workflow_payload` for button clicks.

---

# Test plan

- [x] `message` node — slot substitution in emitted text
- [x] `input` node — prompt on first visit; capture on second message
- [x] Invalid slot — retry message, stay on same node
- [x] `end` node — clears state; next turn hits orchestrator
- [x] Active workflow blocks orchestrator for that turn
- [x] First message with workflows → orchestrator (no auto-start — Phase B)
- [x] LLM `workflow_*` tool → `workflow_enter` with `orchestrator_tool`
