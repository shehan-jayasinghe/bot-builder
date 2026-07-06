import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

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
    turn_id: str | None = None


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


def _tracing_enabled() -> bool:
    return bool(settings.langchain_tracing_v2 and settings.langchain_api_key)


def _build_metadata(context: LlmTracingContext) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "turn_id": context.turn_id,
            "agent_id": context.agent_id,
            "sender_id": context.sender_id,
            "source": context.source,
            "organization_id": context.organization_id,
            "model_id": context.model_id,
            "region": context.region,
        }.items()
        if value
    }


def build_llm_run_config(context: LlmTracingContext | None) -> dict[str, Any] | None:
    if context is None or not _tracing_enabled():
        return None

    metadata = _build_metadata(context)

    return {
        "run_name": f"{context.source}:{context.agent_id}",
        "tags": ["bot-builder", context.source],
        "metadata": metadata,
    }


@asynccontextmanager
async def chat_turn_tracing(
    context: LlmTracingContext,
    *,
    user_message: str,
) -> AsyncIterator[LlmTracingContext]:
    """Open a LangSmith parent run for one chat turn; child LLM/tool runs nest under it."""
    if not _tracing_enabled():
        yield context
        return

    from langsmith.run_helpers import tracing_context
    from langsmith.run_trees import RunTree

    metadata = _build_metadata(context)
    parent = RunTree(
        name=f"chat_turn:{context.source}",
        run_type="chain",
        inputs={"user_message": user_message},
        tags=["bot-builder", context.source, "chat_turn"],
        metadata=metadata,
        project_name=settings.langchain_project,
    )
    parent.post()

    with tracing_context(parent=parent):
        try:
            yield context
            parent.end(outputs={"status": "completed"})
        except Exception as error:
            parent.end(error=str(error))
            raise
