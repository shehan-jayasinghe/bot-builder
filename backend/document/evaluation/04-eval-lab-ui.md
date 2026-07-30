# Eval Lab UI (Phase 3)

Frontend for RAG evaluation — test cases, run eval, metric breakdown panels.

**Status:** Done.

Parent: [00-overview.md](./00-overview.md) · API: [03-evaluation-api.md](./03-evaluation-api.md)

---

## Route

```text
/agent/:agentId/evaluation
```

Implemented as a **standalone page** (not a tab on Preview). Links from [AgentDetailPage](../../frontend/src/pages/agent/AgentDetailPage.tsx) topbar and [AgentPreviewPage](../../frontend/src/pages/agent/AgentPreviewPage.tsx) header.

---

## Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Eval Lab — {agent.name} ({industry} / {agent_type})         │
├────────────────────┬────────────────────────────────────────┤
│ Test cases         │ Metric tabs                            │
│ [+ Add row]        │ Faithfulness | Answer Rel | Ctx Prec | │
│ [Load dummy ▼]   │ Context Recall                         │
│ [Run selected]     │                                        │
│ [Run all]          │  ← panel from GET .../runs/{run_id}    │
└────────────────────┴────────────────────────────────────────┘
```

---

## Left panel — test cases

| Action | API / behavior |
|--------|----------------|
| Add row manually | Local state only (v1 — no **Save dataset** button) |
| Load dummy | `GET .../datasets/dummy` |
| Run one row | `POST .../evaluations/run` → `GET .../runs/{run_id}` |
| Run all | Sequential `POST .../run` per row (batch API deferred 2.11b) |

**Table columns:** Question · Ground truth (optional) · KB scope · Last score · Actions

Pre-fill dummy data from `agent.industry` + `agent.agent_type` (see [03-evaluation-api.md](./03-evaluation-api.md)).

---

## Right panel — metric tabs

### Faithfulness

Matches eval mockup:

- **Left:** Retrieved context chunks + LLM response (red highlight on hallucinated spans)
- **Right:** Claim cards — `grounded` (green) / `hallucinated` (red)
- **Footer:** Score bar, formula `grounded / total`, threshold badge (pass/fail)

Data: `faithfulness_detail` + `turn_evidence` from run detail.

---

### Answer Relevancy

- Generated questions from answer
- Similarity score per question vs original
- Average score 0.0–1.0

Data: `answer_relevancy_detail`

---

### Context Precision

- Ranked chunks list (rank #1, #2, …)
- **Relevant** / **noise** labels from backend breakdown (display only in v1)
- P@k mini bar per rank
- Avg precision score + threshold

Data: `context_precision_detail` + `turn_evidence.rag_retrievals`

---

### Context Recall

- Reference claims from `ground_truth`
- Supported / missing per claim
- Chunk mapping lines

Data: `context_recall_detail` — requires `ground_truth` on test case.

---

## API client

```text
frontend/src/api/evaluation.ts
  runEvaluation(agentId, body)
  listEvalRuns(agentId, params)
  getEvalRun(agentId, runId)
  listEvalDatasets(agentId)
  createEvalDataset(agentId, body)
  getDummyEvalDataset(agentId)
```

Uses React Query — same pattern as [preview.ts](../../frontend/src/api/preview.ts).

**Used by Eval Lab v1:** `runEvaluation`, `getEvalRun`, `getDummyEvalDataset`.

**In API client, not used by UI yet:** `listEvalRuns`, `listEvalDatasets`, `createEvalDataset`.

---

## Components (implemented)

```text
frontend/src/pages/agent/AgentEvaluationPage.tsx
frontend/src/types/evaluation.ts
frontend/src/components/evaluation/
  EvalCaseTable.tsx
  FaithfulnessPanel.tsx
  AnswerRelevancyPanel.tsx
  ContextPrecisionPanel.tsx
  ContextRecallPanel.tsx
  MetricScoreBar.tsx
```

Reuse nested card styling (`#f7f8fa` panels) consistent with `TraceTimeline` / preview panels.

---

## Navigation (implemented)

| Location | Link |
|----------|------|
| Agent detail topbar | **Preview** · **Evaluation** → `/agent/{agentId}/evaluation` |
| Preview header | **Eval Lab** button |

Global sidebar (`MAIN_NAV`) unchanged — eval is per-agent, not a top-level nav item.

---

## Empty / error states

| State | UX |
|-------|-----|
| No KBs on agent | Banner: “Attach knowledge bases for RAG metrics” |
| No RAG call in turn | Faithfulness / Precision show “No retrieval in this run” |
| `RAG_EVAL_ENABLED=false` | Disable run buttons + admin message |
| Missing ground truth | Context Recall tab disabled with hint |

---

## Out of scope (v1 UI)

- Drag-to-reorder chunks affecting live retrieval (display only)
- Export PDF reports
- Compare runs across agents
- Webhook eval (preview/admin only)

---

## Deferred (post–v1 UI)

| Item | Notes |
|------|-------|
| `POST .../evaluations/batch` | Celery async batch (2.11b) |
| Run history panel | `GET .../evaluations/runs` |
| Save custom dataset | `POST .../evaluations/datasets` |
| Chunk label editing | Persist relevant/noise per chunk |
