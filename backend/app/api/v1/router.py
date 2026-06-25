from fastapi import APIRouter

from app.api.v1 import agents, auth, chat, health, knowledgebases

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(knowledgebases.router)
api_v1_router.include_router(chat.router)
