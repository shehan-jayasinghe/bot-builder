from fastapi import APIRouter, Depends

from app.di.auth import get_current_user
from app.domain.catalog.executor_catalog import get_executor_catalog
from app.domain.models.current_user import CurrentUser
from app.schemas.executor import ExecutorCatalogItem, ListExecutorsResponse

router = APIRouter(prefix="/executors", tags=["Executors"])


@router.get("", response_model=ListExecutorsResponse)
async def list_executors(
    current_user: CurrentUser = Depends(get_current_user),
) -> ListExecutorsResponse:
    _ = current_user
    items = [ExecutorCatalogItem(**item) for item in get_executor_catalog()]
    return ListExecutorsResponse(items=items)
