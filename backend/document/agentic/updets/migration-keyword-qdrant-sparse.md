# Migration — Keyword BM25 from local disk to Qdrant sparse vectors

**Status:** Pending

**Prerequisite:** LlamaIndex RAG migration (**Done**) — [migration-llamaindex-rag.md](./migration-llamaindex-rag.md)

**Does not change:** `storage_type` enum, `search_knowledge` tool contract, `RAGRetriever` API, REST KB routes, Mongo `kb_chunks`, vector ingest/query, graph ingest/query, RAGAS evaluation.

---

## Problem

Keyword BM25 indexes are persisted to **local disk** (`{RAG_INDEX_DIR}/{org}/{kb}/bm25/`). This breaks in production:

| Issue | Impact |
|-------|--------|
| Celery worker writes index to its disk | API server cannot read it |
| No shared volume in docker-compose | Worker and API have separate filesystems |
| Container restarts lose indexes | No durable storage |
| Multiple API replicas | Each pod has different/missing indexes |

Vector (Qdrant) and graph (Neo4j) are already remote services — keyword is the only local-disk outlier.

---

## Solution

Move keyword BM25 storage into **Qdrant sparse vectors** — same remote Qdrant already used for dense vector KBs.

| Area | Before (local BM25) | After (Qdrant sparse) |
|------|---------------------|----------------------|
| Keyword ingest | `BM25Retriever.from_defaults()` → `.persist(local_dir)` | Encode chunks as sparse vectors → upsert to Qdrant |
| Keyword query | `BM25Retriever.from_persist_dir(local_dir)` → `.retrieve(query)` | Encode query as sparse vector → Qdrant sparse search |
| Storage | Local files: `corpus.jsonl`, `.npy`, `vocab.index.json`, etc. | Qdrant collection with sparse vector config |
| Durability | Ephemeral container disk | Qdrant persistent volume (already provisioned) |

**No hybrid fusion.** Vector and keyword remain separate `storage_type` values, separate Qdrant collections, separate search paths.

---

## Boundaries (preserved)

| Boundary | Why keep |
|----------|----------|
| `storage_type` enum: `vector`, `keyword`, `graph` | No schema change |
| `RAGRetriever.retrieve()` signature | Chat tool, eval, tests |
| `RagRetrieveResult` / `RagChunk` shape | Turn evidence, RAGAS, trace |
| `format_rag_context()` | `ToolMessage` markdown |
| Collection naming `kb_{org_id}_{kb_id}` | Vector and keyword KBs are different KB records — no collision |
| Mongo `kb_chunks` | Source-of-truth chunk store |
| `search_knowledge` tool schema | Agentic orchestrator unchanged |
| `IndexFactory.index()` / `RetrieverFactory.search()` dispatch | Only keyword branches change internally |

---

## Files to change

### Modified

| File | Change |
|------|--------|
| `infrastructure/ai/llamaindex/index_factory.py` | `index_keyword()` — replace `BM25Retriever.persist(local_dir)` with sparse vector encode + Qdrant upsert |
| `infrastructure/ai/llamaindex/retriever_factory.py` | `retrieve_keyword()` — replace `BM25Retriever.from_persist_dir()` with sparse query encode + Qdrant sparse search |
| `infrastructure/ai/llamaindex/persistence.py` | Remove `keyword_index_dir()` — no longer needed; keep `graph_index_marker()` |
| `infrastructure/connectors/qdrant/qdrant_connector.py` | Add sparse collection creation + sparse upsert + sparse search methods |

### New

| File | Purpose |
|------|---------|
| `infrastructure/ai/llamaindex/keyword_qdrant.py` | BM25 sparse vector encoder (ingest + query) + Qdrant sparse helpers |

### Unchanged

| File | Why |
|------|-----|
| `llama_index_pipeline.py` | Delegates to `IndexFactory` — unchanged |
| `retriever.py` (RAGRetriever) | Calls `RetrieverFactory.search(storage_type=...)` — same API |
| `node_mapping.py` | Hit shape `{text, score, chunk_id}` — same |
| `collection_naming.py` | Reuse `kb_{org}_{kb}` — separate KB records per type |
| `search_knowledge_delegate.py` | Agent tool — unchanged |
| `tool_router.py` | Calls `execute_search_knowledge` — unchanged |
| `config.py` | `rag_index_dir` stays (graph still uses it); no new config needed |
| All vector/graph code | Untouched |

---

## Dependencies (`pyproject.toml`)

No new packages required if using `qdrant-client` sparse vector API directly (already installed). The `llama-index-retrievers-bm25` package can be removed after migration.

Evaluate whether `bm25s` (already in `poetry.lock` as transitive dep) is suitable for sparse encoding, or use a lightweight custom tokenizer + BM25 weight calculator.

---

## Sparse vector format

Qdrant sparse vectors are `{indices: [int], values: [float]}` — a list of token IDs and their BM25 weights.

### Ingest

```text
for each chunk:
  tokens = tokenize(chunk.text)
  sparse_vec = bm25_encode(tokens)  → {indices: [...], values: [...]}
  upsert PointStruct(
    id=chunk_uuid,
    vector={"bm25": SparseVector(indices, values)},
    payload={text, chunk_id, knowledgebase_id, organization_id, metadata},
  )
```

### Query

```text
query_tokens = tokenize(query)
query_sparse = bm25_encode(query_tokens)
results = qdrant.search(
  collection=kb_{org}_{kb},
  query_vector=NamedSparseQuery("bm25", query_sparse),
  limit=top_k,
)
→ map to {text, score, chunk_id}
```

---

## Qdrant collection config (keyword KBs)

Keyword collections use **sparse-only** config (no dense vectors):

```python
client.create_collection(
    collection_name=collection_name,
    vectors_config={},
    sparse_vectors_config={
        "bm25": models.SparseVectorParams(
            modifier=models.Modifier.IDF,
        ),
    },
)
```

This is separate from vector KB collections which use dense-only config.

---

## Implementation checklist

### Step 1 — Sparse encoder + Qdrant helpers

- [ ] `keyword_qdrant.py` — BM25 sparse encoder (tokenize + weight), sparse Qdrant upsert, sparse Qdrant search
- [ ] `qdrant_connector.py` — add `create_sparse_collection()`, `upsert_sparse_points()`, `sparse_search()` (or keep in `keyword_qdrant.py`)

### Step 2 — Wire into factories

- [ ] `index_factory.py` — `index_keyword()` calls new sparse encoder + Qdrant upsert
- [ ] `retriever_factory.py` — `retrieve_keyword()` calls new sparse query + Qdrant search
- [ ] `persistence.py` — remove `keyword_index_dir()` function

### Step 3 — Tests

- [ ] Update `test_llamaindex_index_factory.py` — keyword branch mocks
- [ ] Update `test_llamaindex_retriever_factory.py` — keyword branch mocks
- [ ] Add `test_keyword_qdrant.py` — sparse encode + Qdrant integration

### Step 4 — Cleanup

- [ ] Remove `llama-index-retrievers-bm25` from `pyproject.toml` (if no longer used)
- [ ] Delete `data/rag_indexes/**/bm25/` local directories (ops)
- [ ] Update docs

### Step 5 — Deploy ops (per environment)

- [ ] Re-ingest all `keyword` KBs (creates Qdrant sparse collections)
- [ ] Verify `search_knowledge` trace `chunks` shape for keyword KBs
- [ ] Smoke test keyword search via preview chat

---

## Ops / migration notes

| Risk | Mitigation |
|------|------------|
| Existing keyword KBs have local BM25 files | Re-ingest all `keyword` KBs after deploy |
| Qdrant version must support sparse vectors | Qdrant ≥ v1.7.0 (current docker image is v1.12.5 — supported) |
| BM25 scoring differences | Scores may differ from `llama-index-retrievers-bm25`; `KEYWORD_MIN_SCORE = 0.0` means no filtering impact |
| Collection name collision | Impossible — vector and keyword KBs are different KB records with different IDs |

**No REST or chat API changes.** Deploy = code + re-ingest keyword KBs.

---

## Runtime stack contract (after migration)

| Layer | Implementation |
|-------|----------------|
| Chat agents | LangChain `create_agent()` — unchanged |
| RAG tool | `search_knowledge` → `RAGRetriever` — unchanged API |
| RAG ingest | `LlamaIndexPipeline` → `IndexFactory` |
| RAG query | `RAGRetriever` → `RetrieverFactory` |
| Vector store | Qdrant dense via `llama-index-vector-stores-qdrant` — unchanged |
| **Keyword store** | **Qdrant sparse** via `keyword_qdrant.py` — **changed** |
| Graph store | Neo4j via `llama-index-graph-stores-neo4j` — unchanged |
| Embeddings | Bedrock Titan via `BedrockLlamaEmbedding` — unchanged |
| Eval | RAGAS + `turn_evidence` — unchanged |
