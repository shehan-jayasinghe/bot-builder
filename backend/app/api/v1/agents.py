from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.di.agents import get_agent_service
from app.di.auth import get_current_user
from app.domain.models.current_user import CurrentUser
from app.schemas.agent import (
    AgentStatus,
    CreateAgentRequest,
    CreateAgentResponse,
    GetAgentResponse,
    ListAgentsResponse,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])

AgentIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]


@router.get("", response_model=ListAgentsResponse)
async def list_agents(
    status: AgentStatus | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> ListAgentsResponse:
    return await service.list_by_organization(
        current_user=current_user,
        status=status.value if status else None,
    )


@router.post("", response_model=CreateAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> CreateAgentResponse:
    return await service.create_draft(current_user=current_user, request=body)


@router.get("/{agent_id}", response_model=GetAgentResponse)
async def get_agent(
    agent_id: AgentIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> GetAgentResponse:
    return await service.get_by_id(current_user=current_user, agent_id=agent_id)
