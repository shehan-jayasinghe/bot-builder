# RAG evaluation — overview

RAGAS-style evaluation for agent preview: measure **Faithfulness**, **Answer Relevancy**, **Context Precision**, and **Context Recall** using evidence captured during chat turns.

**Status:** Phase 1 **Done** — Phase 2 **Done** — Phase 3 **Done**.

**Prerequisite:** Agentic RAG via `search_knowledge` (Phase C **Done**). LangGraph session router + `create_agent()` (**Done**).

---

## Problem (before Phase 1) — resolved for evidence capture

| What RAGAS needs | Where it lives now (Phase 1 **Done**) |
|------------------|----------------------------------------|
| User question | `turn_evidence.user_message` + trace `input_message` |
| Assistant answer | `turn_evidence.assistant_replies` (after output gate) |
| Ranked RAG chunks | `turn_evidence.rag_retrievals[]` + `chunks` on `tool_complete` trace |
| Ground truth (optional) | Eval dataset / run request — **Phase 2 Done** |

See [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md).

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
| UI | Eval Lab page (`/agent/:agentId/evaluation`) | All four metric tabs |

**Not on every webhook chat** — eval runs on demand from Eval Lab or batch jobs only.

---

## Phases (3)

| Phase | Scope | Status |
|-------|-------|--------|
| **1** | `turn_evidence` in LangGraph + ranked RAG chunk capture + trace mirror | **Done** |
| **2** | RAGAS service + REST API + Mongo storage + dummy datasets | **Done** |
| **3** | Eval Lab frontend (metrics UI + user test cases) | **Done** |

Details:

- Phase 1 — [01-turn-evidence-runtime.md](./01-turn-evidence-runtime.md)
- Phase 2 — [02-ragas-metrics.md](./02-ragas-metrics.md) · [03-evaluation-api.md](./03-evaluation-api.md)
- Phase 3 — [04-eval-lab-ui.md](./04-eval-lab-ui.md)

---

## Config

| Setting | Env | Default |
|---------|-----|---------|
| `rag_eval_enabled` | `RAG_EVAL_ENABLED` | `false` |
| Judge model | `RAG_EVAL_JUDGE_MODEL_ID` (falls back to `BEDROCK_MODEL_ID`) | agent Bedrock model |
| Faithfulness threshold | `RAG_EVAL_FAITHFULNESS_THRESHOLD` | `0.8` |
| Context precision threshold | `RAG_EVAL_CONTEXT_PRECISION_THRESHOLD` | `0.7` |
| Eval runs collection | `EVAL_RUNS_COLLECTION` | `eval_runs` |
| Eval datasets collection | `EVAL_DATASETS_COLLECTION` | `eval_datasets` |

Turn evidence is always captured on preview/webhook chat turns (Phase 1) — no separate flag.

---

## Dummy datasets

YAML fixtures keyed by `agent.industry` × `agent.agent_type`:

```text
config/eval/datasets/{industry}/{agent_type}.yml
```

Example: `financial_services` + `payment_collections` → savings balance / fee questions with `ground_truth`.

**Shipped fixtures:**

| Path | Profile |
|------|---------|
| `config/eval/datasets/financial_services/payment_collections.yml` | Financial — payment collections |
| `config/eval/datasets/financial_services/customer_onboarding.yml` | Financial — customer onboarding |
| `config/eval/datasets/other/generic.yml` | Fallback when no industry/agent_type match |

Load via `GET .../evaluations/datasets/dummy` — see [03-evaluation-api.md](./03-evaluation-api.md).

---

## End-to-end (builder flow)

1. Enable backend: `RAG_EVAL_ENABLED=true` (+ AWS creds for Bedrock judge/embeddings).
2. Open agent → **Evaluation** (or **Eval Lab** from Preview) → `/agent/{agentId}/evaluation`.
3. **Load dummy** or add test rows (question, optional ground truth, mode, KB scope).
4. **Run selected** or **Run all** → `POST .../evaluations/run` per case → `GET .../evaluations/runs/{run_id}` for metric panels.
5. Review **Faithfulness**, **Answer relevancy**, **Context precision**, **Context recall** tabs.

**API implemented, UI not wired yet:** `GET .../evaluations/runs` (history list), `POST .../evaluations/datasets` (persist custom sets), `POST .../evaluations/batch` (Celery — deferred 2.11b).

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
