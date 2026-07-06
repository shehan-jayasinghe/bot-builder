# RAG evaluation — overview

RAGAS-style evaluation for agent preview: measure **Faithfulness**, **Answer Relevancy**, **Context Precision**, and **Context Recall** using evidence captured during chat turns.

**Status:** Planned — not implemented yet.

**Prerequisite:** Agentic RAG via `search_knowledge` (Phase C **Done**). LangGraph session router + `create_agent()` (**Done**).

---

## Problem today

| What we need for RAGAS | Where it lives now |
|------------------------|-------------------|
| User question | Tracker / trace `input_message` |
| Assistant answer | `ChatGraphResult.replies` |
| Ranked RAG chunks (text, score, rank) | **Missing** — only `chunk_count` on `tool_complete` trace |
| Ground truth (optional) | **Missing** — user/dataset supplied at eval time |

LangGraph state today holds routing flags + replies only — not RAG evidence. See [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md).

---

## Architecture (target)

```text
User / dataset question
    → Preview chat (full bot) OR RAG-only replay
    → LangGraph turn_evidence (question, answer, rag_retrievals[])
    → RAGAS judge (Bedrock LLM)
    → Mongo eval_runs (scores + UI breakdown)
    → Eval Lab UI
```

| Layer | Owner | Notes |
|-------|-------|-------|
| Turn evidence | LangGraph `ChatRouterState.turn_evidence` | Single source for eval input |
| RAG retrieval | `RAGRetriever` + `search_knowledge` | Append ranked chunks to evidence |
| Metrics | RAGAS library + judge LLM | Computed **after** turn — not in graph state |
| Storage | Mongo `eval_runs`, `eval_datasets` | Per agent + org |
| UI | Eval Lab page | Faithfulness / Answer Rel / Context Precision panels |

**Not on every webhook chat** — eval runs on demand from Eval Lab or batch jobs only.

---

## Phases (3)

| Phase | Scope | Status |
|-------|-------|--------|
| **1** | `turn_evidence` in LangGraph + ranked RAG chunk capture + trace mirror | Planned |
| **2** | RAGAS service + REST API + Mongo storage + dummy datasets | Planned |
| **3** | Eval Lab frontend (metrics UI + user test cases) | Planned |

Details:

- Phase 1 — [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md)
- Phase 2 — [02-ragas-metrics.md](./02-ragas-metrics.md) · [03-evaluation-api.md](./03-evaluation-api.md)
- Phase 3 — [04-eval-lab-ui.md](./04-eval-lab-ui.md)

---

## Config (planned)

| Setting | Env | Default |
|---------|-----|---------|
| `rag_eval_enabled` | `RAG_EVAL_ENABLED` | `false` |
| `rag_eval_capture_in_preview` | `RAG_EVAL_CAPTURE_IN_PREVIEW` | `true` |
| Judge model | Reuse agent Bedrock or Haiku profile | — |
| Faithfulness threshold | `RAG_EVAL_FAITHFULNESS_THRESHOLD` | `0.8` |
| Context precision threshold | `RAG_EVAL_CONTEXT_PRECISION_THRESHOLD` | `0.7` |

---

## Dummy datasets

YAML fixtures keyed by `agent.industry` × `agent.agent_type`:

```text
config/eval/datasets/{industry}/{agent_type}.yml
```

Example: `financial_services` + `payment_collections` → savings balance / fee questions with `ground_truth`.

Load via `GET .../evaluations/datasets/dummy` — see [03-evaluation-api.md](./03-evaluation-api.md).

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md) | LangGraph state + chunk capture |
| [02-ragas-metrics.md](./02-ragas-metrics.md) | Metric definitions + judge I/O |
| [03-evaluation-api.md](./03-evaluation-api.md) | REST endpoints |
| [04-eval-lab-ui.md](./04-eval-lab-ui.md) | Frontend Eval Lab |
| [../chat/03-rag-at-chat-diagrams.md](../chat/03-rag-at-chat-diagrams.md) | Current RAG at chat |
| [../chat/01-chat-completion-diagrams.md](../chat/01-chat-completion-diagrams.md) | Chat flow + trace |
| [../agentic/updets/migration-langchain-proper.md](../agentic/updets/migration-langchain-proper.md) | LangChain runtime |
