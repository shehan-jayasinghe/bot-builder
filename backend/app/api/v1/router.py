from fastapi import APIRouter

from app.api.v1 import agents, auth, chat, connectors, executors, health, knowledgebases

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(agents.router)
api_v1_router.include_router(knowledgebases.router)
api_v1_router.include_router(connectors.router)
api_v1_router.include_router(connectors.types_router)
api_v1_router.include_router(executors.router)
api_v1_router.include_router(chat.router)
