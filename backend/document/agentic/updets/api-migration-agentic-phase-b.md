# API migration — Phase B (agentic workflow routing)

**Prerequisite:** [api-migration-agentic.md](./api-migration-agentic.md) Phase A **Done** (capability catalog + `routing_hint` on workflows).

**Runtime spec:** [runtime-migration-agentic-phase-b.md](./runtime-migration-agentic-phase-b.md)

**Goal:** Workflows start only when the **orchestrator LLM** chooses a workflow tool — not via hardcoded first-message auto-start.

---

## Summary

| Category | Count |
|----------|------:|
| REST endpoints — **no change** | **All 37** |
| REST endpoints — schema/service change | **0** |
| **New** REST endpoints | **0** |

Phase B is **runtime-only**. No new URLs, no Pydantic changes.

---

## What changes at chat (not REST)

| Today (pre–Phase B) | After Phase B |
|---------------------|---------------|
| First user message **auto-starts** `workflows[0]` (`default_first_message`) | Orchestrator runs; LLM may call `workflow_<name>` tool |
| `workflow_enter` trace reason `default_first_message` | Only `orchestrator_tool` or `active_state` |
| RAG skipped when auto-start would fire | RAG skipped only when `active_flow_state` is set |

LLM routing uses **existing** Phase A pieces:

- Layer **[3]** capability catalog (workflow `routing_hint` + name/description)
- Workflow delegate tools (`workflow_<normalized_name>`) in `OrchestratorRunner`

---

## Endpoint matrix (all unchanged)

### Chat & preview

| Method | Path | Phase B change |
|--------|------|----------------|
| `POST` | `/api/v1/chat/webhook/{webhook_id}` | **Runtime only** — no schema change. Doc: [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) |
| `POST` | `/api/v1/agents/{agent_id}/preview/chat` | **Runtime only** — same as webhook |
| `GET` | `.../preview/sessions/{sender_id}/trace` | **Optional:** stop emitting `workflow_enter` with `reason: default_first_message` |
| `GET` | `/api/v1/agents/{agent_id}/runtime-graph` | **No change** |

### Workflows (REST — Phase A already done)

| Method | Path | Phase B |
|--------|------|---------|
| `POST` | `/api/v1/workflows` | **No change** — keep setting `routing_hint` when attaching; hints matter **more** for LLM routing |
| `PATCH` | `/api/v1/workflows/{workflow_id}` | **No change** |
| `GET` | `/api/v1/workflows` / `/{id}` | **No change** |
| `POST` | `/api/v1/workflows/{workflow_id}/publish` | **No change** — only `published` workflows in bundle |

Doc: [../../workflows/01-create-workflow-diagrams.md](../../workflows/01-create-workflow-diagrams.md) · [../../workflows/04-update-workflow-diagrams.md](../../workflows/04-update-workflow-diagrams.md)

### Agents, tools, KBs, sub-agents, connectors, auth, health

**No Phase B change.** See [api-migration-agentic.md](./api-migration-agentic.md).

---

## Builder / API consumer notes

| Topic | Phase B impact |
|-------|----------------|
| `routing_hint` on workflows | **Required for good UX** — LLM uses catalog + tool list; empty hints still work but routing is weaker |
| Multiple workflows per agent | LLM picks one via tool call; no implicit “first workflow wins” |
| First message behavior | **Breaking behavior change** for agents that relied on auto-start — document for frontend/QA |
| `ChatRequest` / `ChatResponse` | Unchanged |

---

## Route files — Phase B

| File | Action |
|------|--------|
| `app/api/v1/chat.py` | **No change** |
| `app/api/v1/agents.py` | **No change** |
| `app/api/v1/workflows.py` | **No change** |
| All other `app/api/v1/*.py` | **No change** |

---

## Schema files — Phase B

| File | Action |
|------|--------|
| All `app/schemas/*.py` | **No change** |

---

## Service / repository — Phase B (runtime)

| Component | Change |
|-----------|--------|
| `app/domain/graph/chat_graph.py` | Remove `_should_auto_start_workflow` + `default_first_message` branch |
| `app/services/chat_completion_service.py` | Remove `will_auto_start_workflow`; RAG skip = `in_workflow` only |
| `app/domain/workflow/workflow_delegate.py` | **Optional:** enrich tool `description` with `routing_hint` from catalog |
| `app/domain/graph/orchestrator.py` | **Optional:** pass catalog hints into `build_workflow_delegate_tools` |
| `app/services/workflow_service.py` | **No change** |
| `app/services/runtime_bundle_loader.py` | **No change** |

Detail: [runtime-migration-agentic-phase-b.md](./runtime-migration-agentic-phase-b.md)

---

## Implementation order (Phase B)

1. Remove auto-start from `ChatGraph` + `chat_completion_service`
2. Update / replace tests that assert `default_first_message`
3. **Optional:** workflow tool descriptions include `routing_hint`
4. Update chat + workflow runtime docs; mark Phase B **Done** in [runtime-migration-agentic.md](./runtime-migration-agentic.md)

---

## Tests to add / update

| File | Action |
|------|--------|
| `tests/test_workflow_runtime_at_chat.py` | Remove or rewrite `test_should_auto_start_workflow_*`, `test_chat_graph_auto_starts_hello_workflow` |
| `tests/test_workflow_runtime_at_chat.py` | Add: first message → orchestrator runs, no auto workflow |
| `tests/test_workflow_runtime_at_chat.py` | Keep: LLM `workflow_*` tool → `workflow_enter` with `orchestrator_tool` |
| `tests/test_chat_completion_service.py` | Assert RAG not skipped solely because first message + workflows exist |

---

## Related docs (Phase B annotations)

| Doc | Phase B note |
|-----|----------------|
| [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) | Flow 6 / 11 — remove auto-start |
| [../../chat/04-workflow-runtime-at-chat-diagrams.md](../../chat/04-workflow-runtime-at-chat-diagrams.md) | Flow 1 — enter via LLM tool only |
| [../../chat/06-preview-chat-diagrams.md](../../chat/06-preview-chat-diagrams.md) | Same runtime as webhook |
| [../../workflows/01-create-workflow-diagrams.md](../../workflows/01-create-workflow-diagrams.md) | Emphasize `routing_hint` for LLM |
| [../../workflows/04-update-workflow-diagrams.md](../../workflows/04-update-workflow-diagrams.md) | Same |
