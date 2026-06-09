from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
    }
