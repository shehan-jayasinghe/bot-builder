# Bot Builder

A conversational AI backend platform built around FastAPI, AWS Bedrock, retrieval, workflows, tools, and traceable chat execution.

## Runtime Flow

```text
Chat Request
    |
    v
Chat Handler -> Guardrails -> RAG Retrieval
    |                         |
    +-----------+-------------+
                v
            Chat Graph
                |
        Workflow / Agents
                |
          Bedrock + Tools
                |
          Chat Response
                |
          Trace Persistence
```

## Technology

- Python / FastAPI
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

Swagger is normally available at `http://localhost:8000/docs`.

## Main Capabilities

- LLM-powered chat inference
- Guardrails and validation
- RAG retrieval
- Workflow and graph routing
- Tool execution
- Sub-agent delegation
- Trace and runtime events

## Security

Store model credentials, database credentials, tokens, and other secrets in environment variables or a secret manager. Never commit production credentials.

## Status

The project is evolving toward a broader visual bot-building platform with configuration, workflows, skills, channels, tracing, publishing, and frontend tooling.
