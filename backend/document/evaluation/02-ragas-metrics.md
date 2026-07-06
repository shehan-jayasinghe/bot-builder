# RAGAS metrics (Phase 2)

Metric definitions, inputs, outputs, and judge behavior for the evaluation service.

**Status:** Done.

Parent: [00-overview.md](./00-overview.md) · Evidence: [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md)

---

## Library

- **Package:** `ragas` (`pyproject.toml`)
- **Judge LLM:** AWS Bedrock via `infrastructure/ai/ragas_llm.py` (`RAG_EVAL_JUDGE_MODEL_ID` or `BEDROCK_MODEL_ID`)
- **Embeddings:** Bedrock Titan via same module (answer relevancy)
- **Invocation:** On demand from Eval API — not per webhook chat turn

---

## Inputs (from `turn_evidence`)

| RAGAS field | `turn_evidence` source |
|-------------|------------------------|
| `question` | `user_message` |
| `answer` | Join `assistant_replies` (or first reply) |
| `contexts` | Flatten `rag_retrievals[].chunks[].text` in rank order |
| `ground_truth` | Eval request / dataset only (optional) |

---

## Metrics

### Faithfulness

**Question:** Is the answer supported by retrieved context?

| UI | Backend |
|----|---------|
| Atomic claims list (grounded / hallucinated) | LLM decomposes answer into claims |
| Red highlight on hallucinated spans | Claims with no supporting chunk |
| Score bar + threshold (e.g. > 0.8) | `grounded_claims / total_claims` |

**Requires:** `question`, `answer`, `contexts`  
**Does not require:** `ground_truth`

**Detail payload (`faithfulness_detail`):**

```json
{
  "claims": [
    {
      "text": "Urban minimum is ₹10,000",
      "verdict": "grounded",
      "source_chunk_index": 0
    },
    {
      "text": "Online transfer has no extra charge",
      "verdict": "hallucinated",
      "source_chunk_index": null
    }
  ],
  "score": 0.75
}
```

---

### Answer Relevancy

**Question:** Does the answer address the user question?

| UI | Backend |
|----|---------|
| Generated questions from answer | LLM invents N questions the answer could answer |
| Similarity scores | Cosine similarity vs original `question` |
| Final score 0.0–1.0 | Average similarity |

**Requires:** `question`, `answer`  
**Does not require:** `contexts`, `ground_truth`

**Detail payload (`answer_relevancy_detail`):**

```json
{
  "generated_questions": [
    "What is the urban minimum balance?",
    "What fees apply for non-maintenance?"
  ],
  "similarities": [0.95, 0.72],
  "score": 0.835
}
```

---

### Context Precision

**Question:** Are retrieved chunks relevant and well ranked?

| UI | Backend |
|----|---------|
| Ranked chunks with relevant / noise labels | Relevance per chunk (judge or ground_truth) |
| P@k bars | Precision at each rank |
| Avg precision score | Mean P@k for relevant ranks |

**Requires:** `question`, `contexts`  
**Works better with:** `ground_truth` or manual labels in Eval Lab

**Detail payload (`context_precision_detail`):**

```json
{
  "ranked_chunks": [
    { "rank": 1, "text": "...", "label": "relevant" },
    { "rank": 3, "text": "...", "label": "noise" }
  ],
  "precision_at_k": [1.0, 1.0, 0.67, 0.75, 0.8],
  "score": 0.89
}
```

---

### Context Recall

**Question:** Does context cover the reference answer?

| UI | Backend |
|----|---------|
| Reference claims vs chunks | Map ground_truth claims to chunks |
| Supported / missing badges | Per-claim attribution |
| Score | `supported_claims / total_reference_claims` |

**Requires:** `contexts`, `ground_truth`  
**Optional:** `question`, `answer`

**Detail payload (`context_recall_detail`):**

```json
{
  "reference_claims": [
    { "text": "Urban minimum ₹10,000", "verdict": "supported", "chunk_index": 0 },
    { "text": "Rural minimum ₹2,500", "verdict": "missing", "chunk_index": null }
  ],
  "score": 0.75
}
```

---

## Eval modes

| Mode | Flow | Use case |
|------|------|----------|
| **full_bot** | Preview chat → read `turn_evidence` | End-to-end quality |
| **rag_only** | `RAGRetriever.retrieve()` + optional LLM answer | Isolate retrieval |

---

## Mongo `eval_runs` document

```json
{
  "_id": "...",
  "organization_id": "...",
  "agent_id": "...",
  "mode": "full_bot",
  "question": "...",
  "ground_truth": "...",
  "turn_evidence": { },
  "scores": {
    "faithfulness": 0.75,
    "answer_relevancy": 0.92,
    "context_precision": 0.89,
    "context_recall": 0.80
  },
  "faithfulness_detail": { },
  "answer_relevancy_detail": { },
  "context_precision_detail": { },
  "context_recall_detail": { },
  "status": "complete",
  "created_at": "..."
}
```

---

## Service layout (implemented)

```text
app/domain/evaluation/
  ragas_runner.py           # ragas.aevaluate() + faithfulness claim detail
  metric_breakdown.py       # P@k / recall UI JSON from turn_evidence + scores
  dataset_loader.py         # YAML builtin datasets
app/domain/graph/
  turn_evidence.py          # shared evidence model (Phase 1)
app/services/
  rag_evaluation_service.py
app/infrastructure/ai/
  ragas_llm.py              # Bedrock LLM + embeddings wrappers for RAGAS
app/infrastructure/db/repositories/mongo/
  eval_run_repository.py
  eval_dataset_repository.py
app/schemas/
  evaluation.py             # Pydantic request/response models
app/di/
  evaluation.py             # RagEvaluationService DI
```

---

## Tests (implemented)

| Test file | Covers |
|-----------|--------|
| `tests/test_ragas_runner.py` | Evidence helpers, metric breakdown, mocked `aevaluate` |
| `tests/test_evaluation_api.py` | REST routes (mocked service) |
| `tests/test_dataset_loader.py` | Builtin YAML load + fallback |

---

## Out of scope (v1)

- RAGAS on every production webhook turn
- Blocking chat when score below threshold
- Per-chunk human labeling persistence (optional v2)
- LangSmith eval integration (separate from builder trace)
