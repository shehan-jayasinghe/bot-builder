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
│       ├── domain/           # models, graph, workflow, pipeline
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
  → ChatCompletionService
      → AssistantLoader.try_resolve()
      → RuntimeBundleLoader.load()
      → GuardrailRunner
      → RAGRetriever
      → ChatGraph (workflow / orchestrator routing)
      → OrchestratorRunner → Bedrock LLM + tool execution
  → ChatResponse (text + optional buttons)
```

## Target platform (later — see UI designs)

Full product includes: applications, onboarding, agent config (personality/tone), sub-agents, skills, visual workflows, data sources, channels, trace view, preview, publish.

| Module | Status |
|--------|--------|
| Chat inference + graph routing | Done |
| Assistant loader from MongoDB | Done |
| Guardrails | Done |
| RAG (Qdrant) | Done |
| Tool execution via orchestrator | Done |
| Trace events | Done |
| Workflows runtime | Done |
| Sub-agent delegation | Done |
| Admin / builder APIs | In progress |
| Frontend | In progress |

### Runtime pipeline (per message — target)

1. Input message
2. Guardrails (`guardrail_complete`)
3. RAG (`rag_complete`) — skipped during active workflow
4. ChatGraph routing (workflow / orchestrator / sub-agent)
5. OrchestratorRunner / Bedrock LLM + tool calls
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

## Documentation

- Agentic system (API + runtime migration): [backend/document/agentic/00-overview.md](backend/document/agentic/00-overview.md)
