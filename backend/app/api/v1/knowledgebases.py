from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, UploadFile, status

from app.di.auth import get_current_user
from app.di.knowledgebases import get_knowledgebase_service, parse_create_knowledgebase_request
from app.domain.models.current_user import CurrentUser
from app.schemas.knowledgebase import (
    CreateKnowledgebaseRequest,
    CreateKnowledgebaseResponse,
    KnowledgebaseStatus,
    ListKnowledgebasesResponse,
    UpdateKnowledgebaseRequest,
    UpdateKnowledgebaseResponse,
)
from app.services.knowledgebase_service import KnowledgebaseService

router = APIRouter(prefix="/knowledgebases", tags=["Knowledgebases"])

KnowledgebaseIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]
AgentIdQuery = Query(default=None, pattern=r"^[a-fA-F0-9]{24}$")


@router.get("", response_model=ListKnowledgebasesResponse)
async def list_knowledgebases(
    agent_id: str | None = AgentIdQuery,
    kb_status: KnowledgebaseStatus | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: KnowledgebaseService = Depends(get_knowledgebase_service),
) -> ListKnowledgebasesResponse:
    return await service.list_by_organization(
        current_user=current_user,
        agent_id=agent_id,
        status=kb_status.value if kb_status else None,
    )


@router.post("", response_model=CreateKnowledgebaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledgebase(
    parsed: tuple[CreateKnowledgebaseRequest, UploadFile | None] = Depends(parse_create_knowledgebase_request),
    current_user: CurrentUser = Depends(get_current_user),
    service: KnowledgebaseService = Depends(get_knowledgebase_service),
) -> CreateKnowledgebaseResponse:
    request, file = parsed
    return await service.create(current_user=current_user, request=request, file=file)


@router.patch("/{knowledgebase_id}", response_model=UpdateKnowledgebaseResponse)
async def update_knowledgebase(
    knowledgebase_id: KnowledgebaseIdPath,
    body: UpdateKnowledgebaseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: KnowledgebaseService = Depends(get_knowledgebase_service),
) -> UpdateKnowledgebaseResponse:
    return await service.update(
        current_user=current_user,
        knowledgebase_id=knowledgebase_id,
        request=body,
    )
