# Bot Builder — Backend

FastAPI service for chat inference via AWS Bedrock.

## Learning order

1. `app/api/v1/chat.py` — HTTP entry point
2. `app/core/engine/dialogue.py` — orchestrator
3. `app/core/services/assistant_loader.py` — load bot config
4. `app/core/engine/tracker.py` — session + history
5. `app/core/engine/flow_manager.py` — inference logic
6. `app/ai/llm.py` — AWS Bedrock calls

## Run locally

```bash
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API docs

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
