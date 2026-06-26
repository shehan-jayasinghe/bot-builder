import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.infrastructure.db.mongo import connect_mongo, disconnect_mongo
from app.infrastructure.db.redis import connect_redis, disconnect_redis
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.connector import (
    ConnectionTestFailedError,
    ConnectorNameExistsError,
    ConnectorNotFoundError,
)
from app.shared.exceptions.tool import (
    ToolConnectorTypeMismatchError,
    ToolNameExistsError,
    ToolNotFoundError,
)
from app.shared.exceptions.workflow import WorkflowLimitReachedError
from app.shared.exceptions.auth import (
    AuthError,
    ClerkUserCreationError,
    EmailAlreadyExistsError,
    OrganizationNotFoundError,
    RegistrationFailedError,
    UnauthorizedError,
    UserDisabledError,
    UserNotFoundError,
)

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
    # TODO: connect Qdrant when you add RAG
    logger.info("Starting %s (debug=%s)", settings.app_name, settings.debug)
    await connect_mongo()
    await connect_redis()
    logger.info("Application ready")
    yield
    await disconnect_redis()
    await disconnect_mongo()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(_request: Request, exc: UserNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(AgentNotFoundError)
async def agent_not_found_handler(_request: Request, exc: AgentNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConnectorNotFoundError)
async def connector_not_found_handler(_request: Request, exc: ConnectorNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConnectorNameExistsError)
async def connector_name_exists_handler(_request: Request, exc: ConnectorNameExistsError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ConnectionTestFailedError)
async def connection_test_failed_handler(_request: Request, exc: ConnectionTestFailedError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ToolNotFoundError)
async def tool_not_found_handler(_request: Request, exc: ToolNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ToolNameExistsError)
async def tool_name_exists_handler(_request: Request, exc: ToolNameExistsError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ToolConnectorTypeMismatchError)
async def tool_validation_handler(_request: Request, exc: ToolConnectorTypeMismatchError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(WorkflowLimitReachedError)
async def workflow_limit_reached_handler(_request: Request, exc: WorkflowLimitReachedError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(UserDisabledError)
async def user_disabled_handler(_request: Request, exc: UserDisabledError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(OrganizationNotFoundError)
async def organization_not_found_handler(_request: Request, exc: OrganizationNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(EmailAlreadyExistsError)
async def email_already_exists_handler(_request: Request, exc: EmailAlreadyExistsError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ClerkUserCreationError)
async def clerk_user_creation_handler(_request: Request, exc: ClerkUserCreationError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(RegistrationFailedError)
async def registration_failed_handler(_request: Request, exc: RegistrationFailedError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(AuthError)
async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(api_v1_router, prefix="/api/v1")
