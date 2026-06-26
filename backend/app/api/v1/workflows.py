from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.di.auth import get_current_user
from app.di.workflows import get_workflow_service
from app.domain.models.current_user import CurrentUser
from app.schemas.workflow import (
    CreateWorkflowRequest,
    CreateWorkflowResponse,
    GetWorkflowResponse,
    ListWorkflowsResponse,
    WorkflowStatus,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])

WorkflowIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]
AgentIdQuery = Query(default=None, pattern=r"^[a-fA-F0-9]{24}$")


@router.get("", response_model=ListWorkflowsResponse)
async def list_workflows(
    workflow_status: WorkflowStatus | None = Query(default=None, alias="status"),
    agent_id: str | None = AgentIdQuery,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> ListWorkflowsResponse:
    return await service.list_by_organization(
        current_user=current_user,
        status=workflow_status.value if workflow_status else None,
        agent_id=agent_id,
    )


@router.post("", response_model=CreateWorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: CreateWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> CreateWorkflowResponse:
    return await service.create(current_user=current_user, request=body)


@router.get("/{workflow_id}", response_model=GetWorkflowResponse)
async def get_workflow(
    workflow_id: WorkflowIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> GetWorkflowResponse:
    return await service.get_by_id(current_user=current_user, workflow_id=workflow_id)
