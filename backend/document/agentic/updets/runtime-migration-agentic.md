# Runtime migration — agentic system (non-REST)

Code changes for capability catalog and final prompt assembly. **No new HTTP endpoints.**

API matrix: [api-migration-agentic.md](./api-migration-agentic.md)

---

## Implementation status

**Phase A — implemented** in code (catalog sync + `FinalPromptBuilder` at chat). Phase B **Done**. Phase C **Done**. Phase D **Done**.

**Runtime stack note:** Phases A–D and **LangChain proper** are **Done**. Inner runtime: `create_agent()` + `WorkflowGraphRunner` + LangGraph session router (`chat_router_compiler.py`). See [migration-langchain-proper.md](./migration-langchain-proper.md) and [migration-chat-router-langgraph.md](./migration-chat-router-langgraph.md).

## New files

| File | Purpose |
|------|---------|
| `app/domain/models/capability_catalog.py` | `CapabilityCatalog`, `CapabilityEntry` models |
| `app/domain/pipeline/prompt/capability_catalog_builder.py` | Build layer [3] text from bundle + catalog |
| `app/domain/pipeline/prompt/final_prompt_builder.py` | Assemble layers [1]–[4] |
| `app/domain/graph/search_knowledge_delegate.py` | **Phase C — Done** — LLM `search_knowledge` tool — [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md) |

---

## Update files

| File | Change |
|------|--------|
| `app/services/chat_completion_service.py` | **Done (Phase C):** no pre-turn RAG; **Done (Phase D):** sticky sub-agent — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md) |
| `app/services/runtime_bundle_loader.py` | Load `capability_catalog` from `agent_doc` into `RuntimeBundle` |
| `app/domain/models/runtime_bundle.py` | **Done (Phase D):** `find_sub_agent_by_id()` — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md); `capability_catalog` + legacy `build_system_prompt` |
| `app/domain/graph/orchestrator.py` | **Done (Phase C):** `search_knowledge` tool in `execute_tool_turn` — [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md) |
| `app/domain/graph/chat_graph.py` | **Done (Phase B):** workflow routing; **Done (Phase D):** sticky sub-agent branch — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md) |
| `app/domain/graph/sub_agent_delegate.py` | **Done (Phase C):** `search_knowledge` on sub-agent turns; **Done (Phase D):** sticky + `return_to_orchestrator` — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md) |
| `app/domain/models/tracker.py` | **Done (Phase D):** sticky state via `active_agent_*` + `last_routing_decision` — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md) |
| `app/infrastructure/ai/prompt_builder.py` | Agent create: base `system_prompt` only (role + responsibilities) |
| `app/di/chat.py` | Wire `FinalPromptBuilder` |

---

## Post–Phase A fixes (implemented)

| Fix | Detail |
|-----|--------|
| **Prompt storage** | `build_system_prompt()` stores layer-[1] base only. `personality`, `tone`, `guardrails` stay as separate Mongo fields. |
| **Chat assembly** | `FinalPromptBuilder` adds personality, tone, and `GuardrailRunner.build_instructions()` at runtime. `GuardrailRunner.check()` is pass-through by default; optional NeMo intent gate when `NEMO_GUARDRAILS_ENABLED=true` — [migration-nemo-guardrails.md](./migration-nemo-guardrails.md). |
| **Legacy compat** | If stored `system_prompt` already contains `Personality:`, `Tone:`, or guardrail markers, duplicates are skipped. |
| **Dead code removed** | `OrchestratorRunner._build_system_prompt` removed — chat passes pre-built prompt from `FinalPromptBuilder`. |

---

## Prompt layers (chat turn)

```text
[1] system_prompt + personality/tone   (base prompt from agent doc; personality/tone added at runtime)
[2] guardrail_instructions             (GuardrailRunner.build_instructions)
[3] capability_catalog block           (catalog + RuntimeBundle metadata)
[4] rag_context                        (empty at turn start; chunks via search_knowledge ToolMessage — Phase C Done)
```

---

## Phases

| Phase | Runtime change |
|-------|----------------|
| **A** | Catalog model + `FinalPromptBuilder` + attach sync (see API doc) | **Done** |
| **B** | Remove `ChatGraph._should_auto_start_workflow` — agentic workflow routing | **Done** — [runtime-migration-agentic-phase-b.md](./runtime-migration-agentic-phase-b.md) |
| **C** | `search_knowledge` tool; remove always-on `RAGRetriever.retrieve()` | **Done** — [runtime-migration-agentic-phase-c.md](./runtime-migration-agentic-phase-c.md) |
| **D** | Sticky sub-agent — do not reset to orchestrator every message | **Done** — [runtime-migration-agentic-phase-d.md](./runtime-migration-agentic-phase-d.md) |

---

## Tests

| File | Covers | Status |
|------|--------|--------|
| `tests/test_capability_catalog_builder.py` | Layer [3] text from hints + bundle | **Done** |
| `tests/test_final_prompt_builder.py` | Layer ordering, legacy dedup, no mutation of stored `system_prompt` | **Done** |
| `tests/test_chat_completion_service.py` | Chat completion + orchestrator wiring | **Done** |
| `tests/test_orchestrator_search_knowledge.py` | Phase C — no auto RAG; `search_knowledge` tool loop | **Done** |
