from fastapi import Depends

from app.di.repositories import get_agent_repository, get_connector_repository, get_tool_repository
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.services.tool_service import ToolService


def get_tool_service(
    tool_repository: ToolRepository = Depends(get_tool_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
    connector_repository: ConnectorRepository = Depends(get_connector_repository),
) -> ToolService:
    return ToolService(
        tool_repository=tool_repository,
        agent_repository=agent_repository,
        connector_repository=connector_repository,
    )
