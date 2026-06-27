# RAG at chat — Flow 9

**Not a REST endpoint.** Retrieval runs inside chat completion before orchestrator (today) or via LLM tool (Phase C agentic).

Parent: [01-chat-completion-diagrams.md](./01-chat-completion-diagrams.md) · Flow 9

KB REST (attach + `routing_hint`): [../knowledgebase/01-create-knowledgebase-diagrams.md](../knowledgebase/01-create-knowledgebase-diagrams.md)

**Agentic migration (chat API):** **No** route or schema change. See [../agentic/updets/api-migration-agentic.md](../agentic/updets/api-migration-agentic.md).

**Status:** Implemented — always-on RAG via `RAGRetriever` before orchestrator (skipped during active workflow).

---

## Current flow (always-on)

```mermaid
flowchart TB
    SCOPE[Orchestrator KB list from RuntimeBundle]
    SCOPE --> FILTER[status == ready]
    FILTER --> TYPE{storage_type}
    TYPE -->|vector| Q[Qdrant similarity]
    TYPE -->|keyword| T[TF-IDF search]
    Q --> CTX[rag_context → orchestrator prompt]
    T --> CTX
```

| Component | File |
|-----------|------|
| Retriever | [retriever.py](../../app/domain/pipeline/rag/retriever.py) |
| Wired from | [chat_completion_service.py](../../app/services/chat_completion_service.py) |
| Ingest | [llama_index_pipeline.py](../../app/infrastructure/ai/indexers/llama_index_pipeline.py) |

Scope: orchestrator KBs; sub-agent path can run scoped RAG on delegate.

---

## Agentic migration — Phase C (target)

| Today | Target |
|-------|--------|
| Auto `RAGRetriever.retrieve()` every orchestrator turn | LLM calls `search_knowledge` tool when catalog hint matches |
| Layer [4] injected before LLM | Layer [4] only after tool runs |

`search_knowledge` is an **LLM tool**, not a new REST API.

Runtime spec: [../agentic/updets/runtime-migration-agentic.md](../agentic/updets/runtime-migration-agentic.md)
