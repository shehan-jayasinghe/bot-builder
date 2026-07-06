# Bot Builder — Backend

FastAPI service for chat inference via AWS Bedrock.

## Folder layout

```text
app/
  api/v1/              # HTTP handlers
  schemas/             # API request/response (Pydantic)
  di/                  # Dependency injection (repositories, services, chat)
  services/            # Application services (use cases)
  domain/
    models/            # Tracker, DialogueAssistant, RuntimeBundle
    graph/             # ChatGraph, OrchestratorRunner, langchain/ (create_agent, PII, workflows)
    workflow/          # WorkflowGraphRunner, workflow_graph_compiler, delegates
    pipeline/          # Guardrails, RAG, trace
  infrastructure/
    db/                # mongo, redis, repositories/mongo, repositories/redis
    ai/                # Bedrock LLM, LlamaIndex RAG (llamaindex/)
  shared/              # exceptions, utils
  main.py, config.py
```

## Learning order (chat flow)

1. `app/api/v1/chat.py` — HTTP entry point
2. `app/di/chat.py` — wiring (repos → services → chat completion)
3. `app/services/chat_completion_service.py` — guardrails → final prompt → graph routing → optional NeMo output gate → persist
4. `app/domain/graph/chat_graph.py` — workflow / orchestrator routing
5. `app/services/runtime_bundle_loader.py` — load agent capabilities from MongoDB
6. `app/services/assistant_loader.py` — resolve channel → agent
7. `app/services/tracker_service.py` — session load/save
8. `app/domain/models/tracker.py` — in-memory session state
9. `app/infrastructure/ai/llm.py` — AWS Bedrock

## Pipeline modules

| Module | File | Trace event |
|--------|------|-------------|
| Guardrails (prompt layer [2]) | `domain/pipeline/guardrails/runner.py` — `build_instructions`; NeMo via `nemo_intent_gate.py`, `nemo_output_gate.py`, `scripted_intents.yml` | `guardrail_complete`; `nemo_scripted_reply` / `nemo_intent_blocked` / `nemo_output_complete` / `nemo_output_blocked` when `NEMO_GUARDRAILS_ENABLED=true` |
| PII | `domain/graph/langchain/pii_middleware.py` → `agent_factory.py`; block errors in `orchestrator_agent.py` | (LangChain middleware — no Mongo trace event) |
| RAG | `domain/graph/search_knowledge_delegate.py` + routing middleware | `tool_start` / `tool_complete` for `search_knowledge`; `rag_skipped` when no KBs or in workflow — LlamaIndex ingest/query ([plan](document/agentic/updets/migration-llamaindex-rag.md) **Done**) |
| Builder trace | `domain/pipeline/observability/trace.py` | all events |
| RAG evaluation | `domain/evaluation/` + Eval Lab UI at `/agent/:id/evaluation` | RAGAS on-demand eval — [document/evaluation/00-overview.md](document/evaluation/00-overview.md) **Done** |

## Runtime stack

| Component | Implementation |
|-----------|----------------|
| Intent gate (optional) | NeMo input — `NEMO_GUARDRAILS_ENABLED` (default off); see [migration-nemo-guardrails.md](document/agentic/updets/migration-nemo-guardrails.md) |
| Output gate (optional) | NeMo `self check output` after graph turn — same flag |
| Outer routing | LangGraph `StateGraph` via `ChatGraph` / `chat_router_compiler.py` |
| Orchestrator + sub-agent | LangChain `create_agent()` + `PIIMiddleware` |
| Workflows at chat | LangGraph `StateGraph` via `WorkflowGraphRunner` |
| Executor tools | LangChain `StructuredTool` + agent `ToolNode` |
| PII | LangChain `PIIMiddleware` on agent (email, credit_card, ip, url; block api_key/password/otp) |
| REST APIs | **No URL/schema changes** |

Phases A–D agentic catalog/routing/RAG/sticky sub-agent and LangChain proper migration are **Done** — see [document/agentic/00-overview.md](document/agentic/00-overview.md).

## Run locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API docs

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Agentic migration (API + runtime): [document/agentic/00-overview.md](document/agentic/00-overview.md) — Phases A–D **Done**
- LangChain proper migration (single plan): [document/agentic/updets/migration-langchain-proper.md](document/agentic/updets/migration-langchain-proper.md) — **Done**
- NeMo Guardrails (Phases 0–3): [document/agentic/updets/migration-nemo-guardrails.md](document/agentic/updets/migration-nemo-guardrails.md) — **Done** (off by default)
- RAG evaluation (RAGAS): [document/evaluation/00-overview.md](document/evaluation/00-overview.md) — Phases 1–3 **Done**
- LlamaIndex RAG migration: [document/agentic/updets/migration-llamaindex-rag.md](document/agentic/updets/migration-llamaindex-rag.md) — **Done** (vector + keyword + graph)
