# Bot Builder — local infrastructure

Runs **Qdrant** and **Neo4j** in Docker for local development.

Use your **existing Redis** on the host for Celery (`redis://localhost:6379`).  
Use **AWS cloud S3** and **Bedrock** — not included in this compose file.

## Start

```bash
cd bot-builder/infrastructure/docker
cp .env.example .env
docker compose up -d
```

## Stop

```bash
docker compose down
```

## Services

| Service | URL | Runs in |
|---------|-----|---------|
| Qdrant | http://localhost:6333 | Docker |
| Neo4j | http://localhost:7474 | Docker |
| Redis | localhost:6379 | **Host — already running** |
| S3 | AWS cloud bucket | **AWS — configure in `.env`** |
| Bedrock | AWS API | **AWS — configure in `.env`** |

## Python connector dependencies

Qdrant and Neo4j connectors require optional packages:

```bash
cd bot-builder/backend
poetry add qdrant-client neo4j
```

`S3Connector` and `BedrockConnector` use `boto3` which is already installed.

Copy AWS credentials and bucket name into your backend `.env` (see `.env.example` in this folder).
