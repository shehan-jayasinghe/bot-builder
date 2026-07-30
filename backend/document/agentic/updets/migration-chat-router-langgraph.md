# Migration — ChatGraph outer router → LangGraph

**Status:** Done

**Prerequisite:** [migration-langchain-proper.md](./migration-langchain-proper.md) (**Done**)

**Does not change:** REST APIs, `ChatRequest` / `ChatResponse`, Mongo `Tracker` shape, preview trace events.

---

## Goal

Replace the hand-written `if/else` session router in `ChatGraph` with a compiled LangGraph `StateGraph` that uses **conditional edges** on tracker session state.

| Area | Before | After |
|------|--------|-------|
| Session routing | Python `if/else` in `chat_graph.py` | LangGraph `StateGraph` + conditional edges |
| Priority rules | Same | workflow → sticky sub-agent → orchestrator |
| Inner engines | Unchanged | `create_agent()`, `WorkflowGraphRunner` |
| Tracker | Source of truth | Still source of truth (graph reads/writes via turn context) |

---

## Router graph (target)

```text
START
  → route_by_session (conditional)
       → active_workflow      → END
       → sticky_sub_agent     → END | orchestrator (fallback)
       → orchestrator         → END | workflow_enter
       → workflow_enter       → END
```

| Node | When | Action |
|------|------|--------|
| `active_workflow` | `tracker.active_flow_state` + workflow in bundle | `WorkflowGraphRunner.run_turn` |
| `sticky_sub_agent` | `tracker.active_agent_kind == sub_agent` | `SubAgentRunner.run_turn` |
| `orchestrator` | default | `OrchestratorRunner.run_turn` |
| `workflow_enter` | orchestrator returned `workflow_enter` | enter workflow + first step |

**Fallback:** missing workflow on active state → clear flow → re-route; missing sub-agent → reset → orchestrator.

---

## Files

| File | Action |
|------|--------|
| `domain/graph/chat_router_compiler.py` | **Create** — compile session router `StateGraph` |
| `domain/graph/chat_graph.py` | **Refactor** — invoke compiled router; keep turn helpers |
| `tests/test_langchain_runtime.py` | Assert `StateGraph` in chat router compiler |
| `tests/test_workflow_runtime_at_chat.py` | Unchanged — same `ChatGraph` public API |
| `tests/test_sub_agent_delegation_at_chat.py` | Unchanged |

---

## Done criteria

```text
☑ ChatGraph.run_turn() invokes compiled LangGraph router
☑ Conditional priority: workflow → sticky sub-agent → orchestrator
☑ Orchestrator workflow_enter path preserved
☑ Sticky / missing sub-agent fallback preserved
☑ All chat routing tests pass
☑ No REST API changes
```

## Removed (dead after migrations)

| Path | Reason |
|------|--------|
| `domain/workflow/workflow_runner.py` | Re-export alias — use `workflow_graph_runner.py` |
| `domain/graph/langchain/sub_agent_agent.py` | Unused alias — sub-agent uses `run_tool_agent_turn` |
| `domain/pipeline/safety/` | Custom regex PII — replaced by LangChain `PIIMiddleware` |
| `domain/pipeline/sanitization/` | `pii_redactor.py` removed |
| `domain/pipeline/skills/` | Empty unused directory |

Master index: [../00-overview.md](../00-overview.md)
