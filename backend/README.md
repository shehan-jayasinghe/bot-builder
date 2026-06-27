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
    graph/             # ChatGraph, OrchestratorRunner
    workflow/          # Workflow runner and delegates
    pipeline/          # Guardrails, RAG, trace, sanitization
  infrastructure/
    db/                # mongo, redis, repositories/mongo, repositories/redis
    ai/                # Bedrock LLM, embeddings
  shared/              # exceptions, utils
  main.py, config.py
```

## Learning order (chat flow)

1. `app/api/v1/chat.py` — HTTP entry point
2. `app/di/chat.py` — wiring (repos → services → chat completion)
3. `app/services/chat_completion_service.py` — guardrails → RAG → graph routing → orchestrator
4. `app/domain/graph/chat_graph.py` — workflow / orchestrator routing
5. `app/services/runtime_bundle_loader.py` — load agent capabilities from MongoDB
6. `app/services/assistant_loader.py` — resolve channel → agent
7. `app/services/tracker_service.py` — session load/save
8. `app/domain/models/tracker.py` — in-memory session state
9. `app/infrastructure/ai/llm.py` — AWS Bedrock

## Pipeline modules

| Module | File | Trace event |
|--------|------|-------------|
| Guardrails | `domain/pipeline/guardrails/runner.py` | `guardrail_complete` |
| RAG | `domain/pipeline/rag/retriever.py` | `rag_complete` |
| Trace | `domain/pipeline/observability/trace.py` | all events |

## Run locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API docs

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
