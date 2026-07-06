# Runtime migration — Phase D (sticky sub-agent)

**No new HTTP endpoints.** API matrix: [api-migration-agentic-phase-d.md](./api-migration-agentic-phase-d.md)

**Prerequisite:** Phase A **Done** · Phase B **Done** · Phase C **Done** — [runtime-migration-agentic.md](./runtime-migration-agentic.md)

---

## Implementation status

**Phase D — Done** (implemented in code).

**Runtime stack note:** Sticky sub-agent routing via LangGraph session router (`chat_router_compiler.py`). Orchestrator/sub-agent inner loops use LangChain `create_agent()`. **LangChain proper (Done):** [migration-langchain-proper.md](./migration-langchain-proper.md) · [migration-chat-router-langgraph.md](./migration-chat-router-langgraph.md).

---

## Problem (before Phase D)

Previously every chat turn **reset** sub-agent routing before the orchestrator ran:

```text
turn N:   orchestrator delegates → active_agent_kind = sub_agent → SubAgentRunner reply
turn N+1: chat_completion_service called reset_to_orchestrator() → orchestrator ran again
```

User follow-up messages had to re-trigger delegation through the orchestrator LLM.

**Removed:** per-turn reset block in `chat_completion_service.py`:

```python
# deleted — Phase D
if tracker.active_agent_kind == "sub_agent" and tracker.active_flow_state is None:
    tracker.reset_to_orchestrator()
```

---

## Current behavior (Phase D — Done)

```mermaid
flowchart TB
    MSG[User message]
    MSG --> WF{active_flow_state?}
    WF -->|yes| WFR[WorkflowGraphRunner — priority unchanged]
    WF -->|no| KIND{active_agent_kind?}
    KIND -->|sub_agent| STICKY[SubAgentRunner — sticky follow-up]
    KIND -->|orchestrator| ORCH[OrchestratorRunner]
    ORCH -->|delegate tool| DELEG[SubAgentRunner — first entry]
    DELEG --> SET[tracker.active_agent_kind = sub_agent]
    STICKY --> REPLY[Assistant reply]
    DELEG --> REPLY
    ORCH -->|text| REPLY
```

| Routing | When | Phase D |
|---------|------|---------|
| Reset sub-agent every turn | ~~Start of `chat_completion_service._complete_turn`~~ | **Removed** |
| Sticky sub-agent follow-up | `active_agent_kind == "sub_agent"` and no workflow | **Primary** for turn N+1… |
| Orchestrator | Default or after exit | **Unchanged** |
| Workflow | `active_flow_state` set | **Unchanged** — takes priority over sticky |

---

## Exit conditions (sticky → orchestrator)

| Exit | Mechanism |
|------|-----------|
| Workflow enter | `tracker.enter_workflow()` — workflow path in `ChatGraph` (Phase B) |
| Workflow exit | `tracker.clear_flow_state()` — returns to orchestrator (existing) |
| Explicit return | `return_to_orchestrator` LLM tool on sub-agent turns |
| Session / new topic | Builder may clear session; or orchestrator re-delegates on next explicit delegate tool call after exit |

**MVP:** workflow priority + explicit `return_to_orchestrator` tool. Do not require keyword heuristics.

---

## Code changes (implemented)

### 1. `app/services/chat_completion_service.py`

| Action | Detail |
|--------|--------|
| **Done** | Removed per-turn `reset_to_orchestrator()` when `active_agent_kind == "sub_agent"` |
| **Done** | `sub_agent_continue` trace on sticky turns; `sub_agent_start` on first delegate |

Orchestrator `FinalPromptBuilder` still runs on every turn; sticky path in `ChatGraph` bypasses orchestrator LLM (acceptable MVP cost).

### 2. `app/domain/graph/chat_graph.py`

| Action | Detail |
|--------|--------|
| **Done** | After workflow check: `active_agent_kind == "sub_agent"` → `find_sub_agent_by_id` → `SubAgentRunner.run_turn` |
| **Done** | `delegate_args` from `tracker.last_routing_decision.get("args", {})` on sticky turns |
| **Done** | `ChatGraphResult.routing` with `mode: delegate`, `sticky: true` on follow-up turns |

```python
# Suggested order in run_turn:
# 1. active_flow_state → workflow (existing)
# 2. active_agent_kind == "sub_agent" → SubAgentRunner (Phase D)
# 3. orchestrator (existing)
```

### 3. `app/domain/graph/sub_agent_delegate.py`

| Action | Detail |
|--------|--------|
| **Done** | `return_to_orchestrator` tool on sub-agent turns |
| **Done** | Handler in `execute_tool_turn` — early-return to orchestrator |

### 4. `app/domain/models/runtime_bundle.py`

| Action | Detail |
|--------|--------|
| **Done** | `RuntimeOrchestrator.find_sub_agent_by_id(sub_agent_id: str)` |

### 5. `app/domain/models/tracker.py` — optional (not added)

| Action | Detail |
|--------|--------|
| **Skipped** | `get_sticky_sub_agent_id()` / `get_delegate_args()` — inline `last_routing_decision` in `chat_graph` instead |

Persistence in Mongo via `tracker_repository` already includes `active_agent_id`, `active_agent_kind`, `last_routing_decision` — **no schema migration**.

### 6. No change

| File | Why |
|------|-----|
| `orchestrator.py` | Delegate entry unchanged — first delegate still via orchestrator tool |
| `runtime_bundle_loader.py` | Unchanged |
| `final_prompt_builder.py` | Orchestrator prompt unchanged; sub-agent uses `build_sub_agent_system_prompt` |
| REST routes / schemas | Unchanged |

---

## Prompt / routing on sticky turns

| Turn | System prompt | Tools |
|------|---------------|-------|
| First delegate | `build_sub_agent_system_prompt` + delegate args | sub-agent tools + `search_knowledge` (Phase C) |
| Sticky follow-up | Same sub-agent instructions; delegate args from `last_routing_decision` (or empty) | Same scoped tools |
| Orchestrator | `FinalPromptBuilder` layers [1]–[4] | executor + `search_knowledge` + delegate + `workflow_*` |

Layer [3] catalog on orchestrator turns still lists sub-agents + `routing_hint` for **entry** only.

---

## Trace events

| Event | Phase D change |
|-------|----------------|
| `sub_agent_start` | Emit on **first** delegate from orchestrator (existing — `chat_completion_service.py`) |
| `sub_agent_continue` | **Done** — sticky follow-up; emitted from `chat_completion_service` when `routing.sticky == true` |
| `sub_agent_complete` | Emit after sub-agent reply (existing — `chat_completion_service.py`) |
| `routing_decision` | `mode: delegate` with same `sub_agent_id` on sticky turns |

---

## Tests

| File | Covers | Status |
|------|--------|--------|
| `tests/test_sub_agent_delegation_at_chat.py` | Follow-up does **not** reset; sticky routing | **Done** |
| `tests/test_chat_completion_service.py` | Sticky turn via `ChatGraph` (mocked) | **Done** |
| `tests/test_workflow_runtime_at_chat.py` | Workflow overrides sticky sub-agent | **Done** |
| Return tool test | `return_to_orchestrator` clears sticky state | **Done** |

### Tests removed or rewritten

- ~~`test_chat_completion_resets_sub_agent_before_next_turn`~~ — replaced by sticky follow-up tests

---

## Breaking change notice

Agents that relied on **automatic return to orchestrator** every message will keep users on the sub-agent until explicit exit.

**Mitigation:**

- Document `return_to_orchestrator` for builders
- Preview UI graph highlight will stay on sub-agent node (expected)
- QA multi-turn delegate flows without re-stating the task

---

## After Phase D

Agentic migration phases A–D complete for the current roadmap. Future work (out of scope): executor tool trace events, optional catalog PATCH API.

Master index: [../00-overview.md](../00-overview.md)
