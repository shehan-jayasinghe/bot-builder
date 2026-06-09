# Bot Builder

Greenfield conversational AI backend for ShoutOUT.

## Structure

```text
bot-builder/
├── backend/          # FastAPI + dialogue engine
├── docker-compose.yml
└── README.md
```

## Main flow

```text
Client → POST /api/v1/chat/webhook/{id}
      → DialogueEngine
      → AssistantLoader (config)
      → Tracker (session + history)
      → FlowManager
      → AWS Bedrock
      → JSON chat replies
```

## Quick start

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload
```

Test:

```bash
curl -X POST http://localhost:8000/api/v1/chat/webhook/demo-webhook-id \
  -H "Content-Type: application/json" \
  -d '{"sender_id":"user-1","message":"Hello"}'
```
