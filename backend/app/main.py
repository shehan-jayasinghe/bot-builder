from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.config import settings
from app.db.mongo import connect_mongo, disconnect_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: connect Redis when you add session cache
    # TODO: connect Qdrant when you add RAG
    await connect_mongo()
    yield
    await disconnect_mongo()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_v1_router, prefix="/api/v1")
