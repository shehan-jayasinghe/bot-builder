from fastapi import APIRouter, Depends, UploadFile, status

from app.di.auth import get_current_user
from app.di.knowledgebases import get_knowledgebase_service, parse_create_knowledgebase_request
from app.domain.models.current_user import CurrentUser
from app.schemas.knowledgebase import CreateKnowledgebaseRequest, CreateKnowledgebaseResponse
from app.services.knowledgebase_service import KnowledgebaseService

router = APIRouter(prefix="/knowledgebases", tags=["Knowledgebases"])


@router.post("", response_model=CreateKnowledgebaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledgebase(
    parsed: tuple[CreateKnowledgebaseRequest, UploadFile | None] = Depends(parse_create_knowledgebase_request),
    current_user: CurrentUser = Depends(get_current_user),
    service: KnowledgebaseService = Depends(get_knowledgebase_service),
) -> CreateKnowledgebaseResponse:
    request, file = parsed
    return await service.create(current_user=current_user, request=request, file=file)
