from fastapi import Depends

from app.di.repositories import (
    get_agent_repository,
    get_channel_repository,
    get_tracker_repository,
    get_tracker_session_store,
)
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.channel_repository import ChannelRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.infrastructure.db.repositories.redis.tracker_session_store import TrackerSessionStore
from app.services.assistant_loader import AssistantLoader
from app.services.tracker_service import TrackerService


def get_assistant_loader(
    channel_repository: ChannelRepository = Depends(get_channel_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
) -> AssistantLoader:
    return AssistantLoader(
        channel_repository=channel_repository,
        agent_repository=agent_repository,
    )


def get_tracker_service(
    tracker_repository: TrackerRepository = Depends(get_tracker_repository),
    tracker_session_store: TrackerSessionStore = Depends(get_tracker_session_store),
) -> TrackerService:
    return TrackerService(
        tracker_repository=tracker_repository,
        tracker_session_store=tracker_session_store,
    )
