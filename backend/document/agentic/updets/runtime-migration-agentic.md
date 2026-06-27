# Runtime migration — agentic system (non-REST)

Code changes for capability catalog and final prompt assembly. **No new HTTP endpoints.**

API matrix: [api-migration-agentic.md](./api-migration-agentic.md)

---

## New files

| File | Purpose |
|------|---------|
| `app/domain/models/capability_catalog.py` | `CapabilityCatalog`, `CapabilityEntry` models |
| `app/domain/pipeline/prompt/capability_catalog_builder.py` | Build layer [3] text from bundle + catalog |
| `app/domain/pipeline/prompt/final_prompt_builder.py` | Assemble layers [1]–[4] |
| `app/domain/graph/search_knowledge_delegate.py` | Phase C — LLM `search_knowledge` tool |

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
| `app/di/chat.py` | Wire `FinalPromptBuilder` if using DI |

---

## Prompt layers (chat turn)

```text
[1] system_prompt + personality/tone   (user-owned, from agent doc)
[2] guardrail_instructions             (GuardrailRunner.build_instructions)
[3] capability_catalog block           (catalog + RuntimeBundle metadata)
[4] rag_context                        (Phase C only — after search_knowledge)
```

---

## Phases

| Phase | Runtime change |
|-------|----------------|
| **A** | Catalog model + `FinalPromptBuilder` + attach sync (see API doc) |
| **B** | Remove `ChatGraph._should_auto_start_workflow` — agentic workflow routing |
| **C** | `search_knowledge` tool; remove always-on `RAGRetriever.retrieve()` |
| **D** | Sticky sub-agent — do not reset to orchestrator every message |

---

## Tests to add

| File | Covers |
|------|--------|
| `tests/test_capability_catalog_builder.py` | Layer [3] text from hints + bundle |
| `tests/test_final_prompt_builder.py` | Layer ordering, no mutation of stored `system_prompt` |
| Update `tests/test_chat_completion_service.py` | Final prompt path, RAG skip in workflow |
