from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.di.auth import get_current_user
from app.di.tools import get_tool_service
from app.domain.models.current_user import CurrentUser
from app.schemas.tool import (
    ExecutorName,
    ListToolsResponse,
    ToolStatus,
    UpdateToolRequest,
    UpdateToolResponse,
)
from app.services.tool_service import ToolService

router = APIRouter(prefix="/tools", tags=["Tools"])

ToolIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]
AgentIdQuery = Query(default=None, pattern=r"^[a-fA-F0-9]{24}$")


@router.get("", response_model=ListToolsResponse)
async def list_tools(
    agent_id: str | None = AgentIdQuery,
    executor: ExecutorName | None = Query(default=None),
    tool_status: ToolStatus | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ToolService = Depends(get_tool_service),
) -> ListToolsResponse:
    return await service.list_by_organization(
        current_user=current_user,
        agent_id=agent_id,
        executor=executor.value if executor else None,
        status=tool_status.value if tool_status else None,
    )


@router.patch("/{tool_id}", response_model=UpdateToolResponse)
async def update_tool(
    tool_id: ToolIdPath,
    body: UpdateToolRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ToolService = Depends(get_tool_service),
) -> UpdateToolResponse:
    return await service.update(
        current_user=current_user,
        tool_id=tool_id,
        request=body,
    )
