# Runtime migration — agentic system (non-REST)

Code changes for capability catalog and final prompt assembly. **No new HTTP endpoints.**

API matrix: [api-migration-agentic.md](./api-migration-agentic.md)

---

## Implementation status

**Phase A — implemented** in code (catalog sync + `FinalPromptBuilder` at chat). Phases B–D remain planned.

## New files

| File | Purpose |
|------|---------|
| `app/domain/models/capability_catalog.py` | `CapabilityCatalog`, `CapabilityEntry` models |
| `app/domain/pipeline/prompt/capability_catalog_builder.py` | Build layer [3] text from bundle + catalog |
| `app/domain/pipeline/prompt/final_prompt_builder.py` | Assemble layers [1]–[4] |
| `app/domain/graph/search_knowledge_delegate.py` | **Phase C — not created** — LLM `search_knowledge` tool |

---

## Update files

| File | Change |
|------|--------|
| `app/services/chat_completion_service.py` | Use `FinalPromptBuilder`; stop appending guardrails to `bundle.orchestrator.system_prompt`; Phase C: skip always-on RAG |
| `app/services/runtime_bundle_loader.py` | Load `capability_catalog` from `agent_doc` into `RuntimeBundle` |
| `app/domain/models/runtime_bundle.py` | Add `capability_catalog` field; stop embedding RAG in `build_system_prompt` when using `FinalPromptBuilder` |
| `app/domain/graph/orchestrator.py` | Accept `final_prompt` string; Phase C: register `search_knowledge` tool |
| `app/domain/graph/chat_graph.py` | Phase B: remove `default_first_message` rule — LLM picks workflow from catalog |
| `app/domain/graph/sub_agent_delegate.py` | Use `FinalPromptBuilder` for sub-agent turns; Phase D: sticky handover |
| `app/domain/models/tracker.py` | Phase D: persist active sub-agent across turns |
| `app/infrastructure/ai/prompt_builder.py` | Agent create: base `system_prompt` only (role + responsibilities) |
| `app/di/chat.py` | Wire `FinalPromptBuilder` |

---

## Post–Phase A fixes (implemented)

| Fix | Detail |
|-----|--------|
| **Prompt storage** | `build_system_prompt()` stores layer-[1] base only. `personality`, `tone`, `guardrails` stay as separate Mongo fields. |
| **Chat assembly** | `FinalPromptBuilder` adds personality, tone, and `GuardrailRunner` instructions at runtime. |
| **Legacy compat** | If stored `system_prompt` already contains `Personality:`, `Tone:`, or guardrail markers, duplicates are skipped. |
| **Dead code removed** | `OrchestratorRunner._build_system_prompt` removed — chat passes pre-built prompt from `FinalPromptBuilder`. |

---

## Prompt layers (chat turn)

```text
[1] system_prompt + personality/tone   (base prompt from agent doc; personality/tone added at runtime)
[2] guardrail_instructions             (GuardrailRunner.build_instructions)
[3] capability_catalog block           (catalog + RuntimeBundle metadata)
[4] rag_context                        (always-on today via RAGRetriever; Phase C → search_knowledge tool only)
```

---

## Phases

| Phase | Runtime change |
|-------|----------------|
| **A** | Catalog model + `FinalPromptBuilder` + attach sync (see API doc) | **Done** |
| **B** | Remove `ChatGraph._should_auto_start_workflow` — agentic workflow routing |
| **C** | `search_knowledge` tool; remove always-on `RAGRetriever.retrieve()` |
| **D** | Sticky sub-agent — do not reset to orchestrator every message |

---

## Tests

| File | Covers | Status |
|------|--------|--------|
| `tests/test_capability_catalog_builder.py` | Layer [3] text from hints + bundle | **Done** |
| `tests/test_final_prompt_builder.py` | Layer ordering, legacy dedup, no mutation of stored `system_prompt` | **Done** |
| Update `tests/test_chat_completion_service.py` | Final prompt path, RAG skip in workflow | Partial |
