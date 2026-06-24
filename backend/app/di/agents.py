from fastapi import Depends

from app.di.repositories import get_agent_repository
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.services.agent_service import AgentService


def get_agent_service(
    agent_repository: AgentRepository = Depends(get_agent_repository),
) -> AgentService:
    return AgentService(agent_repository=agent_repository)
