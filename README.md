# Bot Builder

Conversational AI platform backend for ShoutOUT (FastAPI + AWS Bedrock + MongoDB).

## Structure

```text
bot-builder/
├── backend/
│   └── app/
│       ├── api/v1/           # handlers
│       ├── di/               # dependency injection
│       ├── services/         # application services
│       ├── domain/           # models, engine, pipeline
│       ├── infrastructure/   # db (mongo/redis/repos), ai
│       └── schemas/
├── docker-compose.yml
└── README.md
```

## Current scope — chat flow only

Wired today:

```text
POST /api/v1/chat/webhook/{webhook_id}
  → chat.py
  → DialogueEngine.from_channel()
      → AssistantLoader (stub)
      → Tracker (in-memory stub)
  → ChatPipeline
      → GuardrailRunner      (TODO stub)
      → RAGRetriever         (TODO stub)
      → SkillRouter          (TODO stub)
      → TraceCollector       (TODO stub)
      → DialogueEngine.run()
          → FlowManager → Bedrock LLM
  → ChatResponse (text + optional buttons)
```

## Target platform (later — see UI designs)

Full product includes: applications, onboarding, agent config (personality/tone), sub-agents, skills, visual workflows, data sources, channels, trace view, preview, publish.

| Module | Status |
|--------|--------|
| Chat inference + pipeline hooks | In progress |
| Assistant loader from MongoDB | TODO |
| Guardrails | TODO stub |
| RAG (Qdrant) | TODO stub |
| Skills / tool routing | TODO stub |
| Trace API | TODO stub |
| Workflows runtime | TODO |
| Admin / builder APIs | TODO |
| Frontend | TODO |

### Runtime pipeline (per message — target)

1. Input message
2. Guardrails (`guardrail_complete`)
3. RAG (`rag_complete`)
4. Skill / workflow routing (`tool_start`)
5. FlowManager / LLM
6. Rich response (text, buttons, cards)
7. Trace persisted

### Phases

- **Phase 1:** Chat flow + pipeline stubs + Mongo assistant loader
- **Phase 2:** Guardrails, RAG, skills, trace persistence
- **Phase 3:** Workflows, sub-agents, rich UI responses
- **Phase 4:** Admin APIs, data sources, channels, publish
- **Phase 5:** Frontend

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

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
