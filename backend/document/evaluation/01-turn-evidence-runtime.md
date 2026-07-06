# Turn evidence — LangGraph runtime (Phase 1)

Single structured blob per chat turn for RAGAS input. Replaces scattering RAG data across `ToolRouterContext` and trace aggregates.

**Status:** Done.

Parent: [00-overview.md](./00-overview.md)

---

## LangGraph state (Phase 1)

| Graph | State keys |
|-------|------------|
| **Chat router** (`ChatRouterState`) | `finished`, `needs_workflow_enter`, `result`, `turn_evidence` (dict snapshot) |
| **Chat turn context** (`_ChatTurnContext`) | Mutable `TurnEvidence` object — source of truth during the turn |
| **Workflow** (`WorkflowGraphState`) | `current_node_id`, `slots`, `awaiting_slot`, `user_message`, `replies`, `steps`, `exited`, `should_continue` |
| **Orchestrator agent** (`create_agent`) | `messages` only |

**Still on `ToolRouterContext` sidecar:** delegation, workflow-enter signals (not eval evidence).

RAG chunks and tool calls are recorded on **`TurnEvidence`** during `search_knowledge`, then attached to `ChatGraphResult` and persisted on each trace turn.

---

## Target → implemented: `turn_evidence` on `ChatRouterState`

```python
class ChatRouterState(TypedDict, total=False):
    finished: bool
    needs_workflow_enter: bool
    result: Any
    turn_evidence: dict[str, Any] | None = None
```

### `TurnEvidence` shape

```json
{
  "user_message": "What is the minimum balance?",
  "assistant_replies": ["Urban minimum is ₹10,000..."],
  "rag_retrievals": [
    {
      "query": "minimum balance urban",
      "chunks": [
        {
          "rank": 1,
          "text": "Min balance ₹10,000 urban branches",
          "score": 0.91,
          "chunk_id": "abc123",
          "kb_id": "67kb001",
          "kb_name": "savings-policy"
        }
      ]
    }
  ],
  "tool_calls": [
    {
      "name": "search_knowledge",
      "arguments": { "query": "minimum balance urban" },
      "status": "complete"
    }
  ],
  "routing": { "mode": "orchestrator" }
}
```

| Field | Source | Used by |
|-------|--------|---------|
| `user_message` | Chat request | All RAGAS metrics |
| `assistant_replies` | Final graph replies | Faithfulness, Answer Relevancy |
| `rag_retrievals` | `search_knowledge` tool | Faithfulness, Context Precision/Recall |
| `tool_calls` | Agent tool loop | Trace UI, debugging |
| `routing` | `ChatGraphResult.routing` | Eval context (orchestrator vs sub-agent) |

**Not in `turn_evidence`:** RAGAS scores, claim breakdown, Mongo session, system prompt.

---

## Flow

```mermaid
flowchart TB
    START[Chat turn start]
    START --> INIT[Init turn_evidence on ChatRouterState]
    INIT --> GRAPH[ChatGraph path]
    GRAPH --> SK[search_knowledge]
    SK --> APPEND[Append rag_retrievals to turn_evidence]
    APPEND --> REPLY[LLM final reply]
    REPLY --> MERGE[Merge assistant_replies + routing]
    MERGE --> TRACE[Mirror key fields to TraceCollector]
    TRACE --> PERSIST[Snapshot on tracker turn — preview + webhook]
```

---

## Code changes (implemented)

| File | Change |
|------|--------|
| `domain/graph/turn_evidence.py` | **New** — `TurnEvidence` |
| `domain/pipeline/rag/rag_result.py` | **New** — `RagChunk`; `chunks` on `RagRetrieveResult` |
| `domain/graph/chat_router_compiler.py` | `turn_evidence` on `ChatRouterState` |
| `domain/graph/chat_graph.py` | Init evidence; `_attach_turn_evidence()` on result |
| `domain/pipeline/rag/retriever.py` | Populate ranked chunks |
| `domain/graph/langchain/tool_router.py` | Append to evidence + trace `chunks` |
| `domain/graph/langchain/agent_factory.py` | Pass `turn_evidence` into middleware |
| `domain/graph/orchestrator.py`, `sub_agent_delegate.py`, `orchestrator_agent.py` | Thread `turn_evidence` |
| `domain/models/tracker.py`, `trace.py` | `turn_evidence` on finished turn |
| `services/chat_completion_service.py` | Persist evidence after output gate |

---

## `RagRetrieveResult` extension

`RagChunk` lives in `domain/pipeline/rag/rag_result.py`:

```python
@dataclass(frozen=True)
class RagChunk:
    text: str
    rank: int
    kb_id: str
    kb_name: str
    score: float | None = None
    chunk_id: str | None = None
```

`context` stays — formatted string for `ToolMessage`. `chunks` is structured evidence for eval.

---

## Trace mirror (backward compatible)

Extend `tool_complete` for `search_knowledge`:

```json
{
  "tool_name": "search_knowledge",
  "query": "minimum balance",
  "chunk_count": 3,
  "chunks": [{ "rank": 1, "text": "...", "score": 0.91, "kb_id": "..." }]
}
```

Preview trace UI can show chunks without parsing eval DB.

---

## What stays outside state

| Data | Where |
|------|-------|
| RAGAS scores | Mongo `eval_runs` |
| Ground truth | Eval dataset / run request body |
| Tracker session | Mongo + Redis |
| NeMo / PII | Existing pipelines |

---

## Tests (implemented)

| Test file | Covers |
|-----------|--------|
| `tests/test_turn_evidence.py` | `TurnEvidence` recording, retriever chunks, `search_knowledge` + trace |
| `tests/test_orchestrator_search_knowledge.py` | `chunks` + `query` on `tool_complete` trace |
| `tests/test_ragas_runner.py` | RAGAS runner helpers + metric breakdown (Phase 2) |
| `tests/test_evaluation_api.py` | Eval REST routes (Phase 2) |
| `tests/test_dataset_loader.py` | Builtin YAML datasets (Phase 2) |
