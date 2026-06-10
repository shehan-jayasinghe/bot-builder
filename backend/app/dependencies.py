from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.engine.dialogue import DialogueEngine
from app.core.pipeline.chat_pipeline import ChatPipeline
from app.core.services.assistant_loader import AssistantLoader
from app.db.mongo import get_motor_db
from app.db.repositories.agent_repository import AgentRepository
from app.db.repositories.channel_repository import ChannelRepository


def get_channel_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> ChannelRepository:
    return ChannelRepository(db=db)


def get_agent_repository(db: AsyncIOMotorDatabase = Depends(get_motor_db)) -> AgentRepository:
    return AgentRepository(db=db)


def get_assistant_loader(
    channel_repository: ChannelRepository = Depends(get_channel_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
) -> AssistantLoader:
    return AssistantLoader(
        channel_repository=channel_repository,
        agent_repository=agent_repository,
    )


def get_chat_pipeline() -> ChatPipeline:
    return ChatPipeline()


def get_dialogue_engine_factory(
    assistant_loader: AssistantLoader = Depends(get_assistant_loader),
) -> Callable[..., Awaitable[DialogueEngine]]:
    async def factory(
        *,
        webhook_id: str,
        sender_id: str,
        message: str,
        metadata: dict[str, Any],
    ) -> DialogueEngine:
        return await DialogueEngine.from_channel(
            webhook_id=webhook_id,
            sender_id=sender_id,
            message=message,
            metadata=metadata,
            assistant_loader=assistant_loader,
        )

    return factory
