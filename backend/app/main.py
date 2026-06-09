import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.config import settings
from app.db.mongo import connect_mongo, disconnect_mongo

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: connect Redis when you add session cache
    # TODO: connect Qdrant when you add RAG
    logger.info("Starting %s (debug=%s)", settings.app_name, settings.debug)
    await connect_mongo()
    logger.info("Application ready")
    yield
    await disconnect_mongo()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_v1_router, prefix="/api/v1")
