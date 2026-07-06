# Migration — LangChain / LangGraph proper (single plan)

**Status:** Done

**Replaces:** misleading “LangGraph” labels in docs and the **manual** chat runtime (`OrchestratorRunner` loop, custom tool routing, `WorkflowRunner` JSON walker).

**Does not replace:** Phases A–D agentic catalog work (Done). REST APIs stay the same.

**Prerequisite:** Phases A–D **Done** — [../00-overview.md](../00-overview.md)

---

## Goal

Move the **chat runtime** from hand-built Python loops to **LangChain + LangGraph**:

| Area | Today (manual) | Target (LangChain) |
|------|----------------|---------------------|
| Orchestrator LLM + tools | `OrchestratorRunner` — `bind_tools()` + `for` loop | `create_agent()` — compiled LangGraph agent |
| Sub-agent LLM + tools | Same loop via `SubAgentRunner` | `create_agent()` — scoped agent instance |
| Executor tools | `StructuredTool` built in `langgraph_tools.py` | Same tools, wired through agent `ToolNode` |
| Delegate / workflow / RAG tools | Early-return in manual loop | Graph interrupts or pre-tool router in `ChatGraph` |
| Workflows (UI JSON nodes/edges) | `WorkflowRunner` — manual node walker | LangGraph `StateGraph` compiled from workflow JSON |
| Outer session routing | Custom `ChatGraph` (`if/else`) | LangGraph `StateGraph` — [migration-chat-router-langgraph.md](./migration-chat-router-langgraph.md) |
| PII | Custom `redact_pii()` | LangChain `PIIMiddleware` on `create_agent()` |
| Dev observability | LangSmith on single `ainvoke` only | LangSmith **parent run** per chat turn |
| Builder preview trace | Mongo `TraceCollector` | **Keep** — separate from LangSmith |

---

## Honest stack — before vs after

### Before (current code)

```text
ChatCompletionService._complete_turn()
  → GuardrailRunner
  → FinalPromptBuilder
  → ChatGraph (custom Python — NOT langgraph.StateGraph)
       → WorkflowRunner (manual JSON walker)
       → SubAgentRunner → OrchestratorRunner.execute_tool_turn (manual loop)
       → OrchestratorRunner (manual bind_tools + ainvoke loop)
  → Tracker persist + TraceCollector
```

LangGraph package is used for **tool shape only** (`StructuredTool`, unused `ToolNode` helper).

### After (current)

```text
ChatCompletionService._complete_turn()
  → GuardrailRunner.build_instructions()
  → FinalPromptBuilder
  → ChatGraph → chat_router_compiler.py (LangGraph session router)
       → WorkflowGraphRunner.run_turn()  ← LangGraph StateGraph from workflow JSON
       → SubAgentRunner.run_turn()       ← create_agent() + PIIMiddleware
       → OrchestratorRunner.run_turn()   ← create_agent() + PIIMiddleware + middleware
  → Tracker persist + TraceCollector
  → LangSmith parent run (LLM + tools + agent spans)
```

Follow-up router migration: [migration-chat-router-langgraph.md](./migration-chat-router-langgraph.md) (**Done**).

---

## What uses LangGraph after migration

| Component | LangGraph? |
|-----------|:----------:|
| Orchestrator agent | **Yes** — `create_agent()` |
| Sub-agent agent | **Yes** — `create_agent()` |
| Workflows at chat | **Yes** — compiled `StateGraph` per workflow |
| Executor tools | **Yes** — via agent `ToolNode` |
| `ChatGraph` outer router | **Yes** — `chat_router_compiler.py` conditional `StateGraph` |
| Mongo `Tracker` | **No** |
| Preview trace API / UI | **No** — Mongo events |
| LangSmith | **No** — external SaaS; tags only |

---

## REST API impact

| Category | Change |
|----------|--------|
| All existing endpoints | **No URL or schema change** |
| `ChatRequest` / `ChatResponse` | **Unchanged** |
| Preview trace / runtime-graph | **Unchanged** (optional new trace event types) |
| New endpoints | **None** |

---

## Implementation — four steps (one plan, sequential PRs)

### Step 1 — Fix documentation (1 day)

Stop docs claiming LangGraph where code is manual.

**Search/replace in `backend/document/`:**

| Find | Replace with |
|------|--------------|
| `LangGraph routing` | `ChatGraph routing` (custom outer router) |
| `LangGraph tool calling` | `LangChain agent tool calling` |
| `LangGraph tools` (when meaning StructuredTool) | `LangChain StructuredTool` |

**Files to update (Step 1 — Done):**

| File | Change | Status |
|------|--------|--------|
| [../../chat/01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) | Flow 6 title; Flow 7 orchestrator; add “LangChain migration” note | Done |
| [../../chat/04-workflow-runtime-at-chat-diagrams.md](../../chat/04-workflow-runtime-at-chat-diagrams.md) | Remove “Integration with LangGraph routing” — point here | Done |
| [../../chat/06-preview-chat-diagrams.md](../../chat/06-preview-chat-diagrams.md) | OrchestratorAgent not manual loop | Done |
| [../../chat/02-sub-agent-delegation-at-chat-diagrams.md](../../chat/02-sub-agent-delegation-at-chat-diagrams.md) | Sub-agent via create_agent | Done |
| [../../chat/03-rag-at-chat-diagrams.md](../../chat/03-rag-at-chat-diagrams.md) | Manual loop + migration link | Done |
| [../../chat/05-agent-runtime-graph-diagrams.md](../../chat/05-agent-runtime-graph-diagrams.md) | LangChain proper note | Done |
| [../../chat/07-preview-session-trace-diagrams.md](../../chat/07-preview-session-trace-diagrams.md) | LangChain proper note | Done |
| [../../tools/03-execute-tool-at-chat-diagrams.md](../../tools/03-execute-tool-at-chat-diagrams.md) | Tools via LangChain agent | Done |
| [../../workflows/00-workflow-model.md](../../workflows/00-workflow-model.md) | Runtime → LangGraph compiler (planned) | Done |
| [../00-overview.md](../00-overview.md) | Link this doc; runtime stack table | Done |
| [../../../README.md](../../../README.md) | Stack truth table | Done |
| REST API diagram docs (`agent/`, `tools/`, `workflows/`, `sub-agents/`, `knowledgebase/`, `connectors/`) | LangChain proper (Done, no REST change) footer | Done |
| Phase A–D API + runtime docs (`api-migration-agentic*.md`, `runtime-migration-agentic*.md`) | Runtime stack note + fix false LangGraph labels | Done |

**Exit:** No doc implies `StateGraph` or `create_agent` until Step 3–4 are Done.

---

### Step 2 — Upgrade dependencies (1 day) — **Done**

| Package | Action | Resolved |
|---------|--------|----------|
| `langchain` | Add `>=1.3.2` | **1.3.11** |
| `langchain-core` | Bump to version compatible with langchain 1.x | **1.4.8** |
| `langchain-aws` | Verify `ChatBedrockConverse` with new core | **1.6.1** |
| `langgraph` | Verify with `create_agent()` | **1.2.7** (+ `langgraph-prebuilt` **1.1.0**) |

**Files:** `pyproject.toml`, `poetry.lock`

**Exit:** `poetry install` + `pytest` green. No runtime behavior change yet.

---

### Step 3 — Orchestrator + sub-agent + tools (3–5 days) — **Done**

Replace manual LLM tool loop with LangChain agents.

#### New modules

```text
backend/app/domain/graph/langchain/
  __init__.py
  orchestrator_agent.py    # create_agent — shared run_tool_agent_turn (orchestrator + sub-agent)
  tool_router.py           # intercept delegate / workflow_* / return_to_orchestrator
  agent_factory.py         # Bedrock model + middleware + tools assembly
  pii_middleware.py        # PIIMiddleware on create_agent
```

#### Refactor / thin wrappers

| File | Action |
|------|--------|
| [../../../app/domain/graph/orchestrator.py](../../../app/domain/graph/orchestrator.py) | Remove `MAX_TOOL_ITERATIONS` manual loop; delegate to `orchestrator_agent.py` |
| [../../../app/domain/graph/sub_agent_delegate.py](../../../app/domain/graph/sub_agent_delegate.py) | `SubAgentRunner` calls `OrchestratorRunner.execute_tool_turn` → `run_tool_agent_turn` |
| [../../../app/domain/executors/langgraph_tools.py](../../../app/domain/executors/langgraph_tools.py) | Keep `build_langgraph_tool`; wire `ToolNode` in agent graph |
| [../../../app/domain/graph/search_knowledge_delegate.py](../../../app/domain/graph/search_knowledge_delegate.py) | Keep tool; handler in agent tool router |
| [../../../app/domain/workflow/workflow_delegate.py](../../../app/domain/workflow/workflow_delegate.py) | Keep delegate tools; ChatGraph still handles workflow enter |
| [../../../app/domain/graph/chat_graph.py](../../../app/domain/graph/chat_graph.py) | LangGraph session router via `chat_router_compiler.py` |
| [../../../app/services/chat_completion_service.py](../../../app/services/chat_completion_service.py) | Pass `LlmTracingContext` to agent factory |
| [../../../app/di/chat.py](../../../app/di/chat.py) | Inject agent factory |

#### Special tools (behavior must not regress)

| Tool | Today | After Step 3 |
|------|-------|--------------|
| Executor (Mongo/HTTP) | `StructuredTool.ainvoke` | Agent `ToolNode` |
| `search_knowledge` | Custom in `execute_tool_turn` | Custom tool in agent or router |
| `workflow_*` | Early return → `ChatGraph` workflow | `tool_router` → `ChatGraph._enter_and_run_workflow` |
| `delegate_*` | Early return → `SubAgentRunner` | `tool_router` → delegate path |
| `return_to_orchestrator` | Early return | Same via router |

#### Tests to update

| Test file |
|-----------|
| `tests/test_orchestrator_search_knowledge.py` |
| `tests/test_executors.py` |
| `tests/test_chat_completion_service.py` |
| `tests/test_sub_agent_delegation_at_chat.py` |
| `tests/test_workflow_runtime_at_chat.py` |

#### New CI guard

`tests/test_langchain_runtime.py`:

- Assert `create_agent` used in `langchain/orchestrator_agent.py`
- Assert `MAX_TOOL_ITERATIONS` not in `orchestrator.py`

**Exit:** Webhook + preview chat; tools; sub-agent delegate + sticky; workflow enter via orchestrator tool — all pass.

---

### Step 4 — Workflows + PII + LangSmith (Done)

#### Workflows → LangGraph

Replace manual `WorkflowRunner` node walker with a **compiler**:

```text
backend/app/domain/workflow/
  workflow_graph_compiler.py   # Mongo nodes/edges → StateGraph
  workflow_graph_runner.py     # run compiled graph; update tracker.active_flow_state
  slot_validator.py            # used by input nodes
```

| Workflow node type | LangGraph node |
|--------------------|----------------|
| `start` | Entry edge |
| `message` | Node → emit assistant text |
| `input` | Node → interrupt / wait for user; slot capture |
| `output` | Node → reply |
| `end` | Node → clear flow state |

`ChatGraph` sets `tracker.enter_workflow()` and calls `WorkflowGraphRunner`.

**Exit:** All workflow tests in `test_workflow_runtime_at_chat.py` pass on compiled graph.

#### PII — LangChain PIIMiddleware (agent only)

| File | Action |
|------|--------|
| `domain/graph/langchain/pii_middleware.py` | **Create** — built-in `email` redact, `credit_card` mask via `PIIMiddleware` |
| `langchain/agent_factory.py` | `middleware=[*build_agent_pii_middleware(), ...]` on `create_agent()` |

No chat-boundary regex — PII runs inside the agent via LangChain built-in detectors.

#### LangSmith proper

| File | Action |
|------|--------|
| [../../../app/infrastructure/ai/langsmith_tracing.py](../../../app/infrastructure/ai/langsmith_tracing.py) | Parent run per turn; attach `turn_id`, `agent_id`, `sender_id` |
| [../../../app/config.py](../../../app/config.py) | Document tracing flags (keys already exist) |
| [../../../.env.example](../../../.env.example) | Document LangSmith setup |

LangSmith = developer UI at smith.langchain.com. Preview trace = Mongo (unchanged).

**Exit:** LangSmith shows one parent run per chat turn with LLM + tool children.

---

## Full code file checklist

| File | Step | Action |
|------|------|--------|
| `domain/graph/orchestrator.py` | 3 | Refactor — remove manual loop |
| `domain/graph/langchain/*` | 3 | **Create** |
| `domain/graph/sub_agent_delegate.py` | 3 | Wire sub-agent agent |
| `domain/graph/chat_graph.py` | 3–4 | Wire new runners |
| `domain/workflow/workflow_graph_compiler.py` | 4 | **Create** |
| `domain/workflow/workflow_graph_runner.py` | 4 | **Create** |
| `domain/graph/chat_router_compiler.py` | 5 | **Create** — session router LangGraph |
| `domain/executors/langgraph_tools.py` | 3 | Use ToolNode in agent |
| `domain/graph/langchain/pii_middleware.py` | 4 | **Create** |
| `services/chat_completion_service.py` | 3–4 | LangSmith tracing |
| `infrastructure/ai/langsmith_tracing.py` | 4 | Extend |
| `di/chat.py` | 3–4 | Inject factories |
| `pyproject.toml` | 2 | Upgrade deps |
| `tests/test_langchain_runtime.py` | 3 | **Create** |
| `tests/test_pii_middleware.py` | 4 | **Create** |

**Do not change for this migration:** `api/v1/*`, Mongo repositories, frontend, `RuntimeBundleLoader`, builder attach/detach APIs.

---

## Done criteria (whole migration)

```text
☑ Docs match code — no false LangGraph claims (Step 1 Done)
☑ langchain>=1.3 installed; tests green (Step 2 Done — 190 passed)
☑ Orchestrator uses create_agent() — no MAX_TOOL_ITERATIONS loop (Step 3 Done)
☑ Sub-agent uses create_agent() (Step 3 Done — shared run_tool_agent_turn)
☑ Executor tools run through agent ToolNode (Step 3 Done)
☑ Workflows run through compiled LangGraph (`workflow_graph_runner.py`)
☑ Chat session router is LangGraph (`chat_router_compiler.py`) — [migration-chat-router-langgraph.md](./migration-chat-router-langgraph.md)
☑ PIIMiddleware on `create_agent()` — built-in email + credit_card only (no custom regex)
☑ LangSmith parent run per chat turn (chat_turn_tracing + turn_id in metadata)
☑ Webhook + preview + sticky sub-agent + workflow slots — all pass
☑ Dead aliases removed — see **Removed files** below
```

---

## Removed files (dead after migration)

| Path | Reason |
|------|--------|
| `domain/workflow/workflow_runner.py` | Re-export alias — use `workflow_graph_runner.py` |
| `domain/graph/langchain/sub_agent_agent.py` | Unused alias — sub-agent uses `run_tool_agent_turn` |
| `domain/pipeline/safety/` | Custom regex PII — replaced by LangChain `PIIMiddleware` |
| `domain/pipeline/sanitization/` | `pii_redactor.py` removed |
| `domain/pipeline/skills/` | Empty unused directory |

---

## Out of scope (separate future work)

- NVIDIA NeMo Guardrails
- RAGAS agent evaluation
- Per-agent PII config on Mongo agent doc (optional follow-up)
- LangSmith data in preview UI
- Frontend changes

---

## Runtime stack contract (after migration)

| Layer | Implementation |
|-------|----------------|
| HTTP entry | `ChatCompletionService` |
| Safety (PII) | LangChain `PIIMiddleware` on `create_agent()` |
| Prompt | `FinalPromptBuilder` layers [1]–[4] |
| Outer router | LangGraph `StateGraph` via `chat_router_compiler.py` |
| Orchestrator / sub-agent | LangChain `create_agent()` (LangGraph compiled) |
| Workflows | LangGraph `StateGraph` from UI JSON |
| Tools | LangChain `StructuredTool` + `ToolNode` |
| Session | `Tracker` Redis + Mongo |
| Builder trace | `TraceCollector` → preview API |
| Dev LLM trace | LangSmith |

Master index: [../00-overview.md](../00-overview.md)
