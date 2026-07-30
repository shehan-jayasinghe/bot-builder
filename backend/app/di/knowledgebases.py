from typing import Annotated

from fastapi import Depends, File, Form, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.config import settings
from app.di.repositories import (
    get_agent_repository,
    get_job_log_repository,
    get_knowledgebase_repository,
)
from app.infrastructure.connectors.aws.s3_connector import S3Connector
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.job_log_repository import JobLogRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.schemas.knowledgebase import CreateKnowledgebaseRequest, SourceType, StorageType
from app.services.knowledgebase_service import KnowledgebaseService


def get_s3_connector() -> S3Connector:
    return S3Connector(bucket=settings.s3_bucket, region=settings.aws_region)


def get_knowledgebase_service(
    knowledgebase_repository: KnowledgebaseRepository = Depends(get_knowledgebase_repository),
    job_log_repository: JobLogRepository = Depends(get_job_log_repository),
    agent_repository: AgentRepository = Depends(get_agent_repository),
    s3_connector: S3Connector = Depends(get_s3_connector),
) -> KnowledgebaseService:
    return KnowledgebaseService(
        knowledgebase_repository=knowledgebase_repository,
        job_log_repository=job_log_repository,
        agent_repository=agent_repository,
        s3_connector=s3_connector,
    )


async def parse_create_knowledgebase_request(
    name: Annotated[str, Form()],
    source_type: Annotated[SourceType, Form()],
    storage_type: Annotated[StorageType, Form()],
    description: Annotated[str | None, Form()] = None,
    website_url: Annotated[str | None, Form()] = None,
    crawl_depth: Annotated[int | None, Form()] = None,
    agent_id: Annotated[str | None, Form()] = None,
    file: UploadFile | None = File(None),
) -> tuple[CreateKnowledgebaseRequest, UploadFile | None]:
    try:
        request = CreateKnowledgebaseRequest(
            name=name,
            description=description,
            source_type=source_type,
            storage_type=storage_type,
            website_url=website_url,
            crawl_depth=crawl_depth,
            agent_id=agent_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(), body=exc) from exc

    if request.source_type == SourceType.FILE and (file is None or not file.filename):
        raise RequestValidationError(
            [
                {
                    "type": "missing",
                    "loc": ("body", "file"),
                    "msg": "file is required when source_type is file",
                    "input": None,
                }
            ]
        )

    return request, file
