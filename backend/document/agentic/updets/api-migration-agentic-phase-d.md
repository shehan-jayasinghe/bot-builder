# API migration — Phase D (sticky sub-agent)

**Prerequisite:** [api-migration-agentic.md](./api-migration-agentic.md) Phase A **Done**. Phase B **Done** — [api-migration-agentic-phase-b.md](./api-migration-agentic-phase-b.md). Phase C **Done** — [api-migration-agentic-phase-c.md](./api-migration-agentic-phase-c.md).

**Runtime spec:** [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md)

**Goal:** After orchestrator delegates to a sub-agent, **follow-up user messages** stay on that sub-agent until an explicit exit — not reset to orchestrator every turn.

**Status:** **Done** (implemented in code).

---

## Summary

| Category | Count |
|----------|------:|
| REST endpoints — **no change** | **All 37** |
| REST endpoints — schema/service change | **0** |
| **New** REST endpoints | **0** |

Phase D is **runtime-only**. No new URLs, no Pydantic changes.

---

## What changed at chat (not REST)

| Before Phase D | After Phase D (Done) |
|----------------|----------------------|
| Start of every turn: if `active_agent_kind == "sub_agent"` → `tracker.reset_to_orchestrator()` | No per-turn reset — sticky sub-agent state persists |
| Follow-up messages always ran orchestrator LLM first | Follow-up messages run **SubAgentRunner** directly when sticky |
| `active_agent_id` / `active_agent_kind` cleared next message | Persist until **explicit exit** |
| `last_routing_decision.args` only on delegate turn | Reused on sticky follow-up turns |

Workflow priority is **unchanged** (Phase B): `active_flow_state` still routes to `WorkflowRunner` before sub-agent sticky path.

---

## Endpoint matrix (all unchanged)

### Chat & preview

| Method | Path | Phase D change |
|--------|------|----------------|
| `POST` | `/api/v1/chat/webhook/{webhook_id}` | **Runtime only** — no schema change. Doc: [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) |
| `POST` | `/api/v1/agents/{agent_id}/preview/chat` | **Runtime only** — same as webhook |
| `GET` | `.../preview/sessions/{sender_id}/trace` | **Done:** `sub_agent_continue` trace on sticky turns |
| `GET` | `/api/v1/agents/{agent_id}/runtime-graph` | **No change** — graph highlight uses `active_agent_id` (already supported) |

### Sub-agents (REST — Phase A already done)

| Method | Path | Phase D |
|--------|------|---------|
| `POST` | `/api/v1/sub-agents` | **No change** — keep setting `routing_hint` when attaching; hints help orchestrator pick delegate |
| `PATCH` | `/api/v1/sub-agents/{sub_agent_id}` | **No change** |
| `GET` | `/api/v1/sub-agents` / `/{id}` | **No change** |

Doc: [../../sub-agents/01-create-sub-agent-diagrams.md](../../sub-agents/01-create-sub-agent-diagrams.md) · [../../sub-agents/04-update-sub-agent-diagrams.md](../../sub-agents/04-update-sub-agent-diagrams.md)

### Agents, tools, KBs, workflows, connectors, auth, health

**No Phase D change.** See [api-migration-agentic.md](./api-migration-agentic.md).

---

## Builder / API consumer notes

| Topic | Phase D impact |
|-------|----------------|
| `routing_hint` on sub-agents | Orchestrator still uses catalog + delegate tools to **enter** sticky mode |
| Multi-turn sub-agent tasks | **Improved UX** — user can ask follow-ups without re-delegating |
| Session / tracker fields | `active_agent_id`, `active_agent_kind`, `last_routing_decision` already persisted in Mongo — sticky mode relies on them |
| `ChatRequest` / `ChatResponse` | Unchanged |
| Preview graph highlight | Sub-agent node stays highlighted across sticky turns |

---

## Route files — Phase D

| File | Action |
|------|--------|
| `app/api/v1/chat.py` | **No change** |
| `app/api/v1/agents.py` | **No change** |
| `app/api/v1/sub_agents.py` | **No change** |
| All other `app/api/v1/*.py` | **No change** |

---

## Schema files — Phase D

| File | Action |
|------|--------|
| All `app/schemas/*.py` | **No change** |

---

## Service / repository — Phase D (runtime)

| Component | Status |
|-----------|--------|
| `app/services/chat_completion_service.py` | **Done** — no per-turn reset; `sub_agent_continue` trace |
| `app/domain/graph/chat_graph.py` | **Done** — sticky branch → `SubAgentRunner` |
| `app/domain/graph/sub_agent_delegate.py` | **Done** — `return_to_orchestrator` tool |
| `app/domain/models/runtime_bundle.py` | **Done** — `find_sub_agent_by_id()` |
| `app/domain/models/tracker.py` | **Done** — `active_agent_*` + `last_routing_decision` (no new helpers) |
| `app/domain/graph/orchestrator.py` | **No change** — delegate entry unchanged |
| `app/services/tracker_service.py` | **No change** |

Detail: [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md)

---

## Implementation order (Phase D)

1. ~~Remove per-turn `reset_to_orchestrator()` in `chat_completion_service.py`~~ **Done**
2. ~~Add sticky routing in `ChatGraph.run_turn`~~ **Done**
3. ~~Wire `SubAgentRunner` with delegate args from `last_routing_decision`~~ **Done**
4. ~~Exit conditions: workflow, `return_to_orchestrator`, detached sub-agent fallback~~ **Done**
5. ~~Tests + doc annotations; mark Phase D **Done**~~ **Done**

---

## Tests to add / update

| File | Action | Status |
|------|--------|--------|
| `tests/test_sub_agent_delegation_at_chat.py` | Follow-up message stays on sub-agent (no reset) | **Done** |
| `tests/test_sub_agent_delegation_at_chat.py` | Sticky `ChatGraph` + `return_to_orchestrator` tests | **Done** |
| `tests/test_workflow_runtime_at_chat.py` | Workflow still takes priority over sticky sub-agent | **Done** |

---

## Related docs (Phase D annotations)

| Doc | Phase D note |
|-----|----------------|
| [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) | Flow 8 — sticky handover |
| [../../chat/02-sub-agent-delegation-at-chat-diagrams.md](../../chat/02-sub-agent-delegation-at-chat-diagrams.md) | Primary sub-agent runtime spec |
| [../../chat/05-agent-runtime-graph-diagrams.md](../../chat/05-agent-runtime-graph-diagrams.md) | Graph highlight stays on sub-agent |
| [../../chat/06-preview-chat-diagrams.md](../../chat/06-preview-chat-diagrams.md) | Same runtime as webhook |
| [../../chat/07-preview-session-trace-diagrams.md](../../chat/07-preview-session-trace-diagrams.md) | Trace: `sub_agent_continue` on sticky turns |
| [../../sub-agents/01-create-sub-agent-diagrams.md](../../sub-agents/01-create-sub-agent-diagrams.md) | `routing_hint` for orchestrator entry |
| [../../sub-agents/04-update-sub-agent-diagrams.md](../../sub-agents/04-update-sub-agent-diagrams.md) | Same |
| [../../chat/04-workflow-runtime-at-chat-diagrams.md](../../chat/04-workflow-runtime-at-chat-diagrams.md) | Workflow priority over sticky sub-agent |
