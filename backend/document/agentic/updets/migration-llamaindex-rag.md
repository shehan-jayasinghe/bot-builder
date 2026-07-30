# Migration — RAG infrastructure to LlamaIndex (single plan)

**Status:** **Done** — Phases 1–4 complete (vector + keyword + graph ingest/query; legacy code removed).

**Replaced:** custom vector (`QdrantVectorIndex`), keyword (`TfidfIndex`), and graph (`Neo4jGraphIndex`) implementations behind the misnamed `LlamaIndexPipeline` router.

**Does not replace:** LangChain/LangGraph chat runtime, `search_knowledge` tool contract, `RAGRetriever` domain API, REST KB routes, Mongo `kb_chunks`, or RAGAS evaluation.

**Prerequisite:** Phases A–D agentic RAG (**Done**), LangChain proper (**Done**), RAG evaluation (**Done**) — [../00-overview.md](../00-overview.md)

---

## Goal

Consolidate **ingest + retrieval** for all three `storage_type` values into **LlamaIndex**, reducing bespoke index/search code while keeping stable boundaries for chat, trace, and eval.

| Area | Before (custom) | After (LlamaIndex) |
|------|-----------------|---------------------|
| Vector ingest | `QdrantVectorIndex.upsert_chunks` + manual embed loop | `VectorStoreIndex` + `QdrantVectorStore` + `BedrockLlamaEmbedding` |
| Vector query | `VectorSearch` → `QdrantVectorIndex.search` | `RetrieverFactory` → `index.as_retriever()` |
| Keyword ingest | `TfidfIndex.save` (sklearn joblib) | `BM25Retriever.persist` under `RAG_INDEX_DIR` |
| Keyword query | `KeywordSearch` → `TfidfIndex.search` | `BM25Retriever.from_persist_dir` |
| Graph ingest | `Neo4jGraphIndex` — custom Bedrock JSON + Cypher | `PropertyGraphIndex` + `SimpleLLMPathExtractor` + `Neo4jPropertyGraphStore` |
| Graph query | Not implemented (`[]`) | `PropertyGraphIndex.as_retriever(include_text=True)` |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | Unchanged — [chunker.py](../../../app/infrastructure/ai/chunker.py) |
| Multi-KB orchestration | `RAGRetriever` — dedupe, format, error degrade | **Unchanged** — thin facade over `RetrieverFactory` |
| Chat tool | `search_knowledge` | **Unchanged** |
| Eval / turn evidence | `RagChunk`, `turn_evidence.rag_retrievals` | **Unchanged** shape |

---

## Current stack

```text
KnowledgebaseIngestService
  → chunk_documents (LangChain splitter)
  → LlamaIndexPipeline.index()
       → IndexFactory.index(storage_type)
            vector  → VectorStoreIndex + QdrantVectorStore + BedrockLlamaEmbedding
            keyword → BM25Retriever.persist → {RAG_INDEX_DIR}/{org}/{kb}/bm25/
            graph   → PropertyGraphIndex + BedrockLlamaLLM + Neo4jPropertyGraphStore

search_knowledge tool
  → RAGRetriever.retrieve()                # unchanged public API
       → RetrieverFactory.search(storage_type)
       → map NodeWithScore → RagChunk
       → format_rag_context (unchanged)
```

LangChain agents, workflows, and NeMo gates are **out of scope** — see [migration-langchain-proper.md](./migration-langchain-proper.md).

---

## Boundaries (preserved)

| Boundary | Why keep |
|----------|----------|
| `RAGRetriever.retrieve()` signature | Chat tool, eval `rag_only`, tests |
| `RagRetrieveResult` / `RagChunk` | Turn evidence, RAGAS input, trace `chunks` |
| `format_rag_context()` | `### KB name` markdown for `ToolMessage` |
| Collection naming `kb_{org_id}_{kb_id}` | Existing Qdrant collections (re-index if payload schema changed) |
| Mongo `kb_chunks` | Source-of-truth chunk store for UI/debug |
| KB REST + Celery ingest flow | No API/schema change |
| `search_knowledge` tool schema | Orchestrator/sub-agent `create_agent()` tools |

---

## Dependencies (`pyproject.toml`)

```toml
llama-index-core = "^0.14.23"
llama-index-vector-stores-qdrant = "^0.10.2"
llama-index-retrievers-bm25 = "^0.7.1"
llama-index-graph-stores-neo4j = "^0.7.0"
```

Removed: `scikit-learn`, `joblib` (TF-IDF).

---

## Module layout (current)

```text
app/infrastructure/ai/llamaindex/
  bedrock_embedding.py      # BaseEmbedding adapter (Bedrock Titan)
  bedrock_llm.py            # graph triplet extraction
  collection_naming.py      # kb_{organization_id}_{knowledgebase_id}
  chunk_nodes.py            # ChunkDocument → TextNode
  node_mapping.py           # NodeWithScore → {text, score, chunk_id}
  index_factory.py          # ingest per storage_type
  retriever_factory.py      # query per storage_type
  persistence.py            # BM25 + graph.ready paths under RAG_INDEX_DIR
  graph_store.py            # Neo4jPropertyGraphStore builder
  constants.py              # DEFAULT_TOP_K, min scores

app/infrastructure/ai/indexers/llama_index_pipeline.py  # delegates to IndexFactory
app/domain/pipeline/rag/retriever.py                    # factory + dedupe + format
app/domain/pipeline/rag/rag_result.py                   # unchanged
app/infrastructure/connectors/qdrant/                   # health ping, delete collection
app/infrastructure/connectors/neo4j/                    # health ping
```

### Deleted (Phase 4)

| Path | Reason |
|------|--------|
| `infrastructure/vectorstores/qdrant_client.py` | `QdrantVectorStore` |
| `infrastructure/keyword/tfidf_index.py` | `BM25Retriever` |
| `infrastructure/graph/neo4j_client.py` | `PropertyGraphIndex` |
| `domain/pipeline/rag/vector_search.py` | `retriever_factory` |
| `domain/pipeline/rag/keyword_search.py` | `retriever_factory` |
| `infrastructure/ai/bedrock_embeddings.py` | Duplicate of `llamaindex/bedrock_embedding.py` |
| `infrastructure/ai/embeddings.py` | Unused stub |
| Empty `keyword/`, `graph/`, `vectorstores/` packages | No longer needed |

---

## Per storage_type

### `STORAGE_TYPE_VECTOR`

- Ingest: `VectorStoreIndex.from_documents` + `QdrantVectorStore`
- Embed: `BedrockLlamaEmbedding` (Titan)
- Query: `as_retriever(similarity_top_k=5)`, `min_score >= 0.7`

### `STORAGE_TYPE_KEYWORD`

- Ingest: `BM25Retriever.persist` → `{RAG_INDEX_DIR}/{org}/{kb}/bm25/`
- Query: `BM25Retriever.from_persist_dir`, `min_score = 0.0`
- **Ops:** re-ingest keyword KBs — old `.joblib` files incompatible

### `STORAGE_TYPE_GRAPH`

- Ingest: `PropertyGraphIndex.from_documents` + `SimpleLLMPathExtractor` + `BedrockLlamaLLM`
- Store: `Neo4jPropertyGraphStore`; marker `{RAG_INDEX_DIR}/{org}/{kb}/graph.ready`
- Query: `as_retriever(include_text=True)`; ingest capped by `RAG_GRAPH_MAX_CHUNKS` (default 20)

---

## Implementation checklist

### Step 0 — Docs + branch

- [x] This plan
- [x] Branch / PR series

### Step 1 — Dependencies + adapters

- [x] LlamaIndex packages in `pyproject.toml`
- [x] `bedrock_embedding.py`, `bedrock_llm.py`
- [x] `collection_naming.py`, `chunk_nodes.py`, `node_mapping.py`

### Step 2 — Vector

- [x] `index_factory.py` + `retriever_factory.py` vector branches
- [x] Wire `LlamaIndexPipeline` → `IndexFactory`
- [x] Slim `RAGRetriever._search_kb`
- [x] Unit tests

### Step 3 — Keyword

- [x] BM25 ingest + persist
- [x] BM25 retriever
- [x] Delete `TfidfIndex`, `KeywordSearch`

### Step 4 — Graph

- [x] `PropertyGraphIndex` ingest + retriever
- [x] Enable graph path in `retriever.py`
- [x] Unit tests

### Step 5 — Cleanup (Phase 4)

- [x] Delete legacy index/search files
- [x] Remove sklearn + joblib
- [x] Delete `bedrock_embeddings.py`, `embeddings.py`, empty infra packages
- [x] Rename config `tfidf_index_dir` → `rag_index_dir` (`TFIDF_INDEX_DIR` env alias kept)
- [x] Docs updated — **Done**
- [x] Full `pytest` green

### Step 6 — Deploy ops (per environment)

- [ ] Re-ingest all `ready` KBs (vector payload, keyword BM25, graph marker)
- [ ] Verify `search_knowledge` trace `chunks` shape
- [ ] Smoke Eval Lab `rag_only` + `full_bot` runs

---

## Ops / migration notes

| Risk | Mitigation |
|------|------------|
| Qdrant payload schema change | Re-index vector KBs; metadata keys preserved: `chunk_id`, `text`, `knowledgebase_id`, `organization_id` |
| Keyword `.joblib` obsolete | Re-ingest; no auto-migration |
| Graph KBs return data on first query | Expected after re-ingest |
| Bedrock cost on graph ingest | `RAG_GRAPH_MAX_CHUNKS` cap |
| LlamaIndex API churn | Pin versions in `poetry.lock`; adapter layer isolates churn |

**No REST or chat API changes.** Deploy = code + re-index.

---

## Runtime stack contract

| Layer | Implementation |
|-------|----------------|
| Chat agents | LangChain `create_agent()` — unchanged |
| RAG tool | `search_knowledge` → `RAGRetriever` — unchanged API |
| RAG ingest | `LlamaIndexPipeline` → `IndexFactory` (LlamaIndex) |
| RAG query | `RAGRetriever` → `RetrieverFactory` (LlamaIndex) |
| Vector store | Qdrant via `llama-index-vector-stores-qdrant` |
| Keyword store | BM25 persisted per KB under `RAG_INDEX_DIR` |
| Graph store | Neo4j via `llama-index-graph-stores-neo4j` |
| Embeddings | Bedrock Titan via `BedrockLlamaEmbedding` |
| Eval | RAGAS + `turn_evidence` — unchanged |

---

## Out of scope

- Replacing LangChain `create_agent()` with LlamaIndex query engines at chat time
- RAGAS metric or Eval API changes
- Hybrid retrieval (vector + keyword fusion)
- Per-KB retriever tuning UI
- LlamaIndex `SentenceSplitter` instead of LangChain chunker (optional follow-up)

---

## Follow-up: keyword BM25 → Qdrant sparse vectors

Local BM25 disk persistence is not production-safe (Celery worker vs API filesystem, container restarts, multi-replica). Moving keyword storage into **Qdrant sparse vectors** — see [migration-keyword-qdrant-sparse.md](./migration-keyword-qdrant-sparse.md).
