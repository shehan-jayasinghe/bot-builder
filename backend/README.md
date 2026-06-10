# Bot Builder — Backend

FastAPI service for chat inference via AWS Bedrock.

## Folder layout

```text
app/
  api/v1/              # HTTP handlers
  schemas/             # API request/response (Pydantic)
  di/                  # Dependency injection (repositories, services, pipeline, engine)
  services/            # Application services (use cases)
  domain/
    models/            # Tracker, DialogueAssistant
    engine/            # DialogueEngine, FlowManager
    pipeline/          # ChatPipeline, guardrails, RAG, skills, trace
  infrastructure/
    db/                # mongo, redis, repositories/mongo, repositories/redis
    ai/                # Bedrock LLM, embeddings
  shared/              # exceptions, utils
  main.py, config.py
```

## Learning order (chat flow)

1. `app/api/v1/chat.py` — HTTP entry point
2. `app/di/` — wiring (repos → services → factory)
3. `app/domain/pipeline/chat_pipeline.py` — guardrails → RAG → skills → engine
4. `app/domain/engine/dialogue.py` — orchestrator
5. `app/services/assistant_loader.py` — load bot config from MongoDB
6. `app/services/tracker_service.py` — session load/save
7. `app/domain/models/tracker.py` — in-memory session state
8. `app/domain/engine/flow_manager.py` — LLM inference
9. `app/infrastructure/ai/llm.py` — AWS Bedrock

## Pipeline stubs (implement later)

| Module | File | Trace event |
|--------|------|-------------|
| Guardrails | `domain/pipeline/guardrails/runner.py` | `guardrail_complete` |
| RAG | `domain/pipeline/rag/retriever.py` | `rag_complete` |
| Skills | `domain/pipeline/skills/router.py` | `tool_start` |
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
