# Bot Builder

A conversational AI backend platform built with **FastAPI**, **AWS Bedrock**, **MongoDB**, and an agent/workflow-oriented runtime.

## Overview

Bot Builder provides the runtime for processing user messages through guardrails, retrieval, workflow routing, sub-agent delegation, tool execution, and LLM response generation. The current repository is centered on the chat inference flow while the broader product is being developed toward a visual bot-building platform.

## Runtime Architecture

```text
POST /api/v1/chat/webhook/{webhook_id}
              |
              v
          Chat Handler
              |
              v
     ChatCompletionService
              |
       +------+-------+----------------+
       |              |                |
       v              v                v
 Assistant Loader  Guardrails       RAG Retriever
       |              |                |
       +--------------+----------------+
                      |
                      v
                 ChatGraph
                      |
          +-----------+-----------+
          |                       |
          v                       v
     Workflow                Orchestrator
                                  |
                                  v
                       Bedrock LLM + Tools
                                  |
                                  v
                       Rich Chat Response
                                  |
                                  v
                           Trace Persistence
```

## Current Runtime Pipeline

1. Receive the chat message.
2. Resolve the assistant configuration from MongoDB.
3. Load the runtime bundle.
4. Run guardrails.
5. Retrieve relevant knowledge through the RAG layer when applicable.
6. Route the message through `ChatGraph`.
7. Execute workflows, orchestrator logic, or sub-agent delegation.
8. Call AWS Bedrock and tools when required.
9. Return text and optional rich UI actions such as buttons/cards.
10. Persist trace events.

## Main Components

```text
backend/app/
├── api/v1/           # API handlers
├── di/               # Dependency injection
├── services/         # Application services
├── domain/           # Domain models and workflow/graph concepts
├── infrastructure/   # MongoDB, Redis, repositories and AI integrations
└── schemas/          # Request/response schemas
```

## AI Capabilities

The repository includes the following runtime capabilities:

- AWS Bedrock LLM integration
- Guardrails
- Retrieval-augmented generation (RAG)
- LlamaIndex-based retrieval
- Vector, keyword and graph retrieval approaches
- Tool execution
- Workflow runtime
- Sub-agent delegation
- Trace events

## Product Roadmap

| Capability | Status |
|---|---|
| Chat inference and graph routing | Done |
| MongoDB assistant loading | Done |
| Guardrails | Done |
| RAG | Done |
| Tool execution | Done |
| Trace events | Done |
| Workflow runtime | Done |
| Sub-agent delegation | Done |
| Admin / builder APIs | In progress |
| Frontend | In progress |

## Technology Stack

- Python
- FastAPI
- AWS Bedrock
- LlamaIndex
- MongoDB
- Redis
- Docker
- Poetry

## Quick Start

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload
```

Test the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat/webhook/demo-webhook-id \
  -H "Content-Type: application/json" \
  -d '{"sender_id":"user-1","message":"Hello"}'
```

Useful endpoints:

- Swagger UI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Documentation

Additional architecture and migration documentation lives under `backend/document/`, including the agentic runtime and LlamaIndex RAG migration.

## Development Status

The repository is actively evolving from a chat-runtime implementation toward a complete bot-builder platform with application management, agent configuration, skills, workflows, data sources, channels, tracing, preview, publishing, and a frontend builder.
