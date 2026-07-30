from fastapi import Depends

from app.di.repositories import (
    get_agent_repository,
    get_knowledgebase_repository,
    get_sub_agent_repository,
    get_tool_repository,
    get_workflow_repository,
)
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.sub_agent_repository import SubAgentRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.services.sub_agent_service import SubAgentService


def get_sub_agent_service(
    sub_agent_repository: SubAgentRepository = Depends(get_sub_agent_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
    tool_repository: ToolRepository = Depends(get_tool_repository),
    knowledgebase_repository: KnowledgebaseRepository = Depends(get_knowledgebase_repository),
    workflow_repository: WorkflowRepository = Depends(get_workflow_repository),
) -> SubAgentService:
    return SubAgentService(
        sub_agent_repository=sub_agent_repository,
        agent_repository=agent_repository,
        tool_repository=tool_repository,
        knowledgebase_repository=knowledgebase_repository,
        workflow_repository=workflow_repository,
    )
