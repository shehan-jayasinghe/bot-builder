import logging
import os
from dataclasses import dataclass
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmTracingContext:
    agent_id: str
    sender_id: str
    source: str
    organization_id: str | None = None
    model_id: str | None = None
    region: str | None = None


def configure_langsmith() -> None:
    """Sync LangChain/LangSmith env vars from application settings."""
    if not settings.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return

    if not settings.langchain_api_key:
        logger.warning(
            "LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is empty; "
            "LangSmith tracing will remain off.",
        )
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

    logger.info("LangSmith tracing enabled for project=%s", settings.langchain_project)


def build_llm_run_config(context: LlmTracingContext | None) -> dict[str, Any] | None:
    if context is None or not settings.langchain_tracing_v2 or not settings.langchain_api_key:
        return None

    metadata = {
        key: value
        for key, value in {
            "agent_id": context.agent_id,
            "sender_id": context.sender_id,
            "source": context.source,
            "organization_id": context.organization_id,
            "model_id": context.model_id,
            "region": context.region,
        }.items()
        if value
    }

    return {
        "run_name": f"{context.source}:{context.agent_id}",
        "tags": ["bot-builder", context.source],
        "metadata": metadata,
    }
