# Bot Builder — Backend

FastAPI service for chat inference via AWS Bedrock.

## Learning order (chat flow)

1. `app/api/v1/chat.py` — HTTP entry point
2. `app/core/pipeline/chat_pipeline.py` — guardrails → RAG → skills → engine
3. `app/core/engine/dialogue.py` — orchestrator
4. `app/core/services/assistant_loader.py` — load bot config (stub)
5. `app/core/engine/tracker.py` — session + history (stub)
6. `app/core/engine/flow_manager.py` — LLM inference
7. `app/ai/llm.py` — AWS Bedrock

## Pipeline stubs (implement later)

| Module | File | Trace event |
|--------|------|-------------|
| Guardrails | `core/guardrails/runner.py` | `guardrail_complete` |
| RAG | `core/rag/retriever.py` | `rag_complete` |
| Skills | `core/skills/router.py` | `tool_start` |
| Trace | `core/observability/trace.py` | all events |

## Run locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API docs

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
