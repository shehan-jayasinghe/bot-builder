# API migration — Phase C (agentic RAG)

**Prerequisite:** [api-migration-agentic.md](./api-migration-agentic.md) Phase A **Done** (`routing_hint` on KBs). Phase B **Done** — [api-migration-agentic-phase-b.md](./api-migration-agentic-phase-b.md).

**Runtime spec:** [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md)

**Goal:** Knowledge retrieval runs only when the LLM calls a `search_knowledge` tool (orchestrator and sub-agent turns) — not via always-on `RAGRetriever.retrieve()` before every turn.

**Status:** **Done** (implemented in code).

**Runtime stack note:** `search_knowledge` runs inside LangChain `create_agent()` via routing middleware. **LangChain proper (Done):** [migration-langchain-proper.md](./migration-langchain-proper.md). **No REST change.**

---

## Summary

| Category | Count |
|----------|------:|
| REST endpoints — **no change** | **All 37** |
| REST endpoints — schema/service change | **0** |
| **New** REST endpoints | **0** |

Phase C is **runtime-only**. No new URLs, no Pydantic changes.

---

## What changes at chat (not REST)

| Before Phase C | Current (Done) |
|----------------------|---------------|
| `chat_completion_service` calls `RAGRetriever.retrieve()` before orchestrator when KBs attached | No pre-turn RAG; `FinalPromptBuilder` layer [4] empty at turn start |
| Layer [4] `rag_context` in system prompt every orchestrator turn | Retrieved chunks returned via `search_knowledge` **tool message** in LLM loop |
| `rag_complete` / `rag_skipped` trace on every turn | `tool_start` / `tool_complete` for `search_knowledge`; embed RAG stats in `tool_complete` (no separate per-turn `rag_complete` before LLM) |
| `rag_skipped` when orchestrator turn has KBs | `rag_skipped` only when `in_workflow` or no KBs attached (trace-only; no pre-turn retrieve) |
| Sub-agent delegation auto-runs RAG for sub-agent KBs | **Required:** sub-agent path also tool-driven via `search_knowledge` on `SubAgentRunner` turn (see runtime spec) |

LLM routing uses **existing** Phase A pieces:

- Layer **[3]** capability catalog (KB `routing_hint` + name/description)
- New `search_knowledge` LangChain `StructuredTool` when orchestrator has attached KBs

---

## Endpoint matrix (all unchanged)

### Chat & preview

| Method | Path | Phase C change |
|--------|------|----------------|
| `POST` | `/api/v1/chat/webhook/{webhook_id}` | **Runtime only** — no schema change. Doc: [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) |
| `POST` | `/api/v1/agents/{agent_id}/preview/chat` | **Runtime only** — same as webhook |
| `GET` | `.../preview/sessions/{sender_id}/trace` | **Optional:** `tool_complete` for `search_knowledge` includes RAG metadata (replaces per-turn `rag_complete`) |
| `GET` | `/api/v1/agents/{agent_id}/runtime-graph` | **No change** |

### Knowledge bases (REST — Phase A already done)

| Method | Path | Phase C |
|--------|------|---------|
| `POST` | `/api/v1/knowledgebases` | **No change** — keep setting `routing_hint` when attaching; hints matter **more** for LLM tool choice |
| `PATCH` | `/api/v1/knowledgebases/{knowledgebase_id}` | **No change** |
| `GET` | `/api/v1/knowledgebases` / `/{id}` | **No change** |

Doc: [../../knowledgebase/01-create-knowledgebase-diagrams.md](../../knowledgebase/01-create-knowledgebase-diagrams.md) · [../../knowledgebase/04-update-knowledgebase-agent-diagrams.md](../../knowledgebase/04-update-knowledgebase-agent-diagrams.md)

### Agents, tools, workflows, sub-agents, connectors, auth, health

**No Phase C change.** See [api-migration-agentic.md](./api-migration-agentic.md).

---

## Builder / API consumer notes

| Topic | Phase C impact |
|-------|----------------|
| `routing_hint` on knowledge bases | **Important for UX** — LLM uses catalog + tool list to decide when to search |
| Agents with KBs but no hints | Tool still works; model may under-search |
| First message behavior | **Breaking change** for agents that relied on silent always-on RAG — answers may lack KB context until LLM calls tool |
| `ChatRequest` / `ChatResponse` | Unchanged |
| Ingest / indexing REST | Unchanged — only **query path** at chat becomes agentic |

---

## Route files — Phase C

| File | Action |
|------|--------|
| `app/api/v1/chat.py` | **No change** |
| `app/api/v1/agents.py` | **No change** |
| `app/api/v1/knowledgebases.py` | **No change** |
| All other `app/api/v1/*.py` | **No change** |

---

## Schema files — Phase C

| File | Action |
|------|--------|
| All `app/schemas/*.py` | **No change** |

---

## Service / repository — Phase C (runtime)

| Component | Change |
|-----------|--------|
| `app/services/chat_completion_service.py` | **Remove** always-on `RAGRetriever.retrieve()` for orchestrator path; pass `rag_context=""` to `FinalPromptBuilder` |
| `app/domain/graph/search_knowledge_delegate.py` | **Add** — `build_search_knowledge_tool()` LangChain `StructuredTool` (stub coroutine; real logic in `execute_tool_turn`) |
| `app/domain/graph/orchestrator.py` | Register `search_knowledge` when orchestrator has KBs; invoke `RAGRetriever` in `execute_tool_turn`; remove auto sub-agent RAG prefetch |
| `app/domain/graph/sub_agent_delegate.py` | **Update** `SubAgentRunner.run_turn` — register `search_knowledge` when sub-agent has KBs; stop pre-fetched `rag_context` in prompt |
| `app/domain/pipeline/prompt/final_prompt_builder.py` | Layer [4] only when explicitly passed (empty at turn start after Phase C) |
| `app/domain/pipeline/rag/retriever.py` | **No change** — reused by tool handler |
| `app/services/knowledgebase_service.py` | **No change** |
| `app/services/runtime_bundle_loader.py` | **No change** |

Detail: [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md)

---

## Implementation order (Phase C)

1. Add `search_knowledge_delegate.py` (stub tool) + wire real handler in `OrchestratorRunner.execute_tool_turn`
2. Remove pre-turn RAG block from `chat_completion_service.py`; keep `skip_rag` for trace only (`rag_skipped` when `in_workflow` or no KBs)
3. **Required:** remove orchestrator sub-agent auto-RAG prefetch; add `search_knowledge` on `SubAgentRunner` turns when sub-agent has KBs
4. Update / add tests (no auto RAG; tool invokes retriever)
5. Update chat + RAG runtime docs; mark Phase C **Done** in [runtime-migration-agentic.md](./runtime-migration-agentic.md)

---

## Tests to add / update

| File | Action | Status |
|------|--------|--------|
| `tests/test_chat_completion_service.py` | No auto `retrieve` when KBs attached — see `test_orchestrator_search_knowledge.py` | **Done** |
| `tests/test_search_knowledge_delegate.py` (new) | Tool description includes KB `routing_hint` from catalog | **Done** |
| `tests/test_orchestrator_search_knowledge.py` | `test_chat_completion_does_not_auto_retrieve_rag_with_kbs` + handler + LLM tool loop | **Done** |
| `tests/test_sub_agent_delegation_at_chat.py` | Sub-agent — no prefetch; `search_knowledge` tool registered when KBs exist | **Done** |
| `tests/test_rag_retriever.py` | **Keep** — retriever unit tests unchanged | **Done** |

---

## Related docs (Phase C annotations)

| Doc | Phase C note |
|-----|----------------|
| [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) | Flow 9 — agentic RAG tool |
| [../../chat/03-rag-at-chat-diagrams.md](../../chat/03-rag-at-chat-diagrams.md) | Primary RAG runtime spec |
| [../../chat/02-sub-agent-delegation-at-chat-diagrams.md](../../chat/02-sub-agent-delegation-at-chat-diagrams.md) | Sub-agent `search_knowledge` on `SubAgentRunner` |
| [../../chat/05-agent-runtime-graph-diagrams.md](../../chat/05-agent-runtime-graph-diagrams.md) | No REST change |
| [../../chat/06-preview-chat-diagrams.md](../../chat/06-preview-chat-diagrams.md) | Same runtime as webhook |
| [../../chat/07-preview-session-trace-diagrams.md](../../chat/07-preview-session-trace-diagrams.md) | Trace: `tool_complete` for RAG, not per-turn `rag_complete` |
| [../../knowledgebase/01-create-knowledgebase-diagrams.md](../../knowledgebase/01-create-knowledgebase-diagrams.md) | Emphasize `routing_hint` for LLM |
| [../../knowledgebase/04-update-knowledgebase-agent-diagrams.md](../../knowledgebase/04-update-knowledgebase-agent-diagrams.md) | Same |
