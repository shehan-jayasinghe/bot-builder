from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "bot-builder"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "bot_builder"

    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600
    tracker_collection: str = "trackers"

    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
