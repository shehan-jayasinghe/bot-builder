from fastapi import APIRouter, Depends, status

from app.di.auth import get_current_user
from app.di.workflows import get_workflow_service
from app.domain.models.current_user import CurrentUser
from app.schemas.workflow import CreateWorkflowRequest, CreateWorkflowResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=CreateWorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: CreateWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> CreateWorkflowResponse:
    return await service.create(current_user=current_user, request=body)
