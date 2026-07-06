# Eval Lab UI (Phase 3)

Frontend for RAG evaluation — test cases, run eval, metric breakdown panels.

**Status:** Planned.

Parent: [00-overview.md](./00-overview.md) · API: [03-evaluation-api.md](./03-evaluation-api.md)

---

## Route

```text
/agents/:agentId/evaluation
```

Alternative: tab on existing [AgentPreviewPage](../../frontend/src/pages/agent/AgentPreviewPage.tsx) — **Eval** next to Chat / Graph / Trace.

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

| Action | API |
|--------|-----|
| Add row manually | Local state → `POST .../datasets` on save |
| Load dummy | `GET .../datasets/dummy` |
| Run one row | `POST .../evaluations/run` |
| Run all | `POST .../evaluations/batch` |

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
- Toggle **relevant** / **noise** (v2: persist labels)
- P@k mini chart per rank
- Avg precision score + threshold

Data: `context_precision_detail` + `turn_evidence.rag_retrievals`

---

### Context Recall

- Reference claims from `ground_truth`
- Supported / missing per claim
- Chunk mapping lines

Data: `context_recall_detail` — requires `ground_truth` on test case.

---

## API client (planned)

```text
frontend/src/api/evaluation.ts
  runEvaluation(agentId, body)
  listEvalRuns(agentId, params)
  getEvalRun(agentId, runId)
  listDatasets(agentId)
  createDataset(agentId, body)
  getDummyDataset(agentId)
```

Use React Query — same pattern as [preview.ts](../../frontend/src/api/preview.ts).

---

## Components (planned)

```text
frontend/src/pages/agent/AgentEvaluationPage.tsx
frontend/src/components/evaluation/
  EvalCaseTable.tsx
  FaithfulnessPanel.tsx
  AnswerRelevancyPanel.tsx
  ContextPrecisionPanel.tsx
  ContextRecallPanel.tsx
  MetricScoreBar.tsx
```

Reuse dark card styling from `TraceTimeline` / `PreviewChatPanel`.

---

## Navigation

Add to agent sidebar or agent detail sub-nav:

```text
Preview | Evaluation | Settings ...
```

Update [constants/navigation.ts](../../frontend/src/constants/navigation.ts) if global nav entry needed.

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

## Implementation order

1. API client + `AgentEvaluationPage` shell
2. Test case table + `POST /run`
3. Faithfulness panel (richest UI)
4. Answer Relevancy + Context Precision
5. Context Recall + batch run + run history list
