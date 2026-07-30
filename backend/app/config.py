from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "bot-builder"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "bot_builder"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    redis_session_ttl: int = 3600
    tracker_collection: str = "trackers"

    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    clerk_secret_key: str = ""
    clerk_issuer: str = ""
    clerk_jwks_url: str = ""
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    users_collection: str = "users"
    organizations_collection: str = "organizations"
    knowledgebases_collection: str = "knowledgebases"
    job_logs_collection: str = "job_logs"

    s3_bucket: str = "bot-builder-kb"
    kb_chunks_collection: str = "kb_chunks"

    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_embed_dimensions: int = 1024

    # LangSmith / LangChain tracing — one parent run per chat turn when enabled
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "bot-builder"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # NeMo Guardrails — intent + output gates (off by default)
    nemo_guardrails_enabled: bool = False
    nemo_config_path: str = ""

    # RAG evaluation (RAGAS) — on-demand eval API (off by default)
    rag_eval_enabled: bool = False
    rag_eval_faithfulness_threshold: float = 0.8
    rag_eval_context_precision_threshold: float = 0.7
    rag_eval_judge_model_id: str = ""
    eval_runs_collection: str = "eval_runs"
    eval_datasets_collection: str = "eval_datasets"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    neo4j_database: str = "neo4j"

    rag_index_dir: str = Field(
        default="data/rag_indexes",
        validation_alias=AliasChoices("RAG_INDEX_DIR", "TFIDF_INDEX_DIR"),
    )

    rag_graph_max_chunks: int = Field(
        default=20,
        validation_alias=AliasChoices("RAG_GRAPH_MAX_CHUNKS"),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
