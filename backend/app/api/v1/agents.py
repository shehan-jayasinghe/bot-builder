from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.di.agents import get_agent_service
from app.di.auth import get_current_user
from app.di.knowledgebases import get_knowledgebase_service
from app.di.preview import get_runtime_graph_service
from app.di.chat import get_chat_completion_service
from app.di.sub_agents import get_sub_agent_service
from app.di.tools import get_tool_service
from app.domain.models.current_user import CurrentUser
from app.schemas.agent import (
    AgentStatus,
    CreateAgentRequest,
    CreateAgentResponse,
    GetAgentResponse,
    ListAgentsResponse,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.knowledgebase import KnowledgebaseStatus, ListKnowledgebasesResponse
from app.schemas.preview import RuntimeGraphResponse
from app.schemas.sub_agent import (
    CreateSubAgentRequest,
    CreateSubAgentResponse,
    GetSubAgentResponse,
    ListSubAgentsResponse,
    SubAgentStatus,
    UpdateSubAgentRequest,
    UpdateSubAgentResponse,
)
from app.schemas.tool import (
    CreateToolRequest,
    CreateToolResponse,
    ExecutorName,
    GetToolResponse,
    ListToolsResponse,
    ToolStatus,
)
from app.services.agent_service import AgentService
from app.services.chat_completion_service import ChatCompletionService
from app.services.knowledgebase_service import KnowledgebaseService
from app.services.runtime_graph_service import RuntimeGraphService
from app.services.sub_agent_service import SubAgentService
from app.services.tool_service import ToolService

router = APIRouter(prefix="/agents", tags=["Agents"])

AgentIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]
ToolIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]
SubAgentIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]


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


@router.get("/{agent_id}/knowledgebases", response_model=ListKnowledgebasesResponse)
async def list_agent_knowledgebases(
    agent_id: AgentIdPath,
    status: KnowledgebaseStatus | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    service: KnowledgebaseService = Depends(get_knowledgebase_service),
) -> ListKnowledgebasesResponse:
    return await service.list_by_agent(
        current_user=current_user,
        agent_id=agent_id,
        status=status.value if status else None,
    )


@router.post("/{agent_id}/tools", response_model=CreateToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    agent_id: AgentIdPath,
    body: CreateToolRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ToolService = Depends(get_tool_service),
) -> CreateToolResponse:
    return await service.create(current_user=current_user, agent_id=agent_id, request=body)


@router.get("/{agent_id}/tools", response_model=ListToolsResponse)
async def list_agent_tools(
    agent_id: AgentIdPath,
    executor: ExecutorName | None = Query(default=None),
    tool_status: ToolStatus | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ToolService = Depends(get_tool_service),
) -> ListToolsResponse:
    return await service.list_by_agent(
        current_user=current_user,
        agent_id=agent_id,
        executor=executor.value if executor else None,
        status=tool_status.value if tool_status else None,
    )


@router.get("/{agent_id}/tools/{tool_id}", response_model=GetToolResponse)
async def get_tool(
    agent_id: AgentIdPath,
    tool_id: ToolIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: ToolService = Depends(get_tool_service),
) -> GetToolResponse:
    return await service.get_by_id(
        current_user=current_user,
        agent_id=agent_id,
        tool_id=tool_id,
    )


@router.post(
    "/{agent_id}/sub-agents",
    response_model=CreateSubAgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sub_agent(
    agent_id: AgentIdPath,
    body: CreateSubAgentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SubAgentService = Depends(get_sub_agent_service),
) -> CreateSubAgentResponse:
    return await service.create(current_user=current_user, agent_id=agent_id, request=body)


@router.get("/{agent_id}/sub-agents", response_model=ListSubAgentsResponse)
async def list_sub_agents(
    agent_id: AgentIdPath,
    sub_agent_status: SubAgentStatus | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: SubAgentService = Depends(get_sub_agent_service),
) -> ListSubAgentsResponse:
    return await service.list_by_agent(
        current_user=current_user,
        agent_id=agent_id,
        status=sub_agent_status.value if sub_agent_status else None,
    )


@router.get("/{agent_id}/sub-agents/{sub_agent_id}", response_model=GetSubAgentResponse)
async def get_sub_agent(
    agent_id: AgentIdPath,
    sub_agent_id: SubAgentIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: SubAgentService = Depends(get_sub_agent_service),
) -> GetSubAgentResponse:
    return await service.get_by_id(
        current_user=current_user,
        agent_id=agent_id,
        sub_agent_id=sub_agent_id,
    )


@router.patch("/{agent_id}/sub-agents/{sub_agent_id}", response_model=UpdateSubAgentResponse)
async def update_sub_agent(
    agent_id: AgentIdPath,
    sub_agent_id: SubAgentIdPath,
    body: UpdateSubAgentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SubAgentService = Depends(get_sub_agent_service),
) -> UpdateSubAgentResponse:
    return await service.update(
        current_user=current_user,
        agent_id=agent_id,
        sub_agent_id=sub_agent_id,
        request=body,
    )


@router.get("/{agent_id}/runtime-graph", response_model=RuntimeGraphResponse)
async def get_agent_runtime_graph(
    agent_id: AgentIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: RuntimeGraphService = Depends(get_runtime_graph_service),
) -> RuntimeGraphResponse:
    return await service.get_runtime_graph(current_user=current_user, agent_id=agent_id)


@router.post("/{agent_id}/preview/chat", response_model=ChatResponse)
async def preview_chat(
    agent_id: AgentIdPath,
    body: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatCompletionService = Depends(get_chat_completion_service),
) -> ChatResponse:
    return await service.complete_preview(
        agent_id=agent_id,
        organization_id=current_user.organization_id,
        request=body,
    )


@router.get("/{agent_id}", response_model=GetAgentResponse)
async def get_agent(
    agent_id: AgentIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> GetAgentResponse:
    return await service.get_by_id(current_user=current_user, agent_id=agent_id)
