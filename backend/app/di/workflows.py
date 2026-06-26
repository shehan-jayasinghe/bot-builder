from fastapi import Depends

from app.di.repositories import get_agent_repository, get_workflow_repository
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.services.workflow_service import WorkflowService


def get_workflow_service(
    workflow_repository: WorkflowRepository = Depends(get_workflow_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
) -> WorkflowService:
    return WorkflowService(
        workflow_repository=workflow_repository,
        agent_repository=agent_repository,
    )
