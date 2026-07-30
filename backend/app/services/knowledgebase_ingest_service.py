import asyncio
import logging
import os

from app.config import settings
from app.domain.constants.knowledgebase_constants import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    KB_STATUS_CHUNKING,
    KB_STATUS_EXTRACTING,
    KB_STATUS_FAILED,
    KB_STATUS_INDEXING,
    KB_STATUS_READY,
    SOURCE_TYPE_FILE,
    SOURCE_TYPE_WEBSITE,
)
from app.domain.models.source_document import SourceDocument
from app.infrastructure.ai.chunker import chunk_documents
from app.infrastructure.ai.file_parser import parse_file_bytes
from app.infrastructure.ai.indexers.llama_index_pipeline import LlamaIndexPipeline
from app.infrastructure.ai.web_scraper import scrape_website
from app.infrastructure.connectors.aws.s3_connector import S3Connector
from app.infrastructure.db.mongo import get_motor_db
from app.infrastructure.db.repositories.mongo.job_log_repository import JobLogRepository
from app.infrastructure.db.repositories.mongo.kb_chunk_repository import KbChunkRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.schemas.knowledgebase import IngestKnowledgebasePayload

logger = logging.getLogger(__name__)


class KnowledgebaseIngestService:
    def __init__(
        self,
        *,
        knowledgebase_repository: KnowledgebaseRepository,
        job_log_repository: JobLogRepository,
        kb_chunk_repository: KbChunkRepository,
        s3_connector: S3Connector,
        indexer: LlamaIndexPipeline,
    ) -> None:
        self._knowledgebase_repository = knowledgebase_repository
        self._job_log_repository = job_log_repository
        self._kb_chunk_repository = kb_chunk_repository
        self._s3_connector = s3_connector
        self._indexer = indexer

    async def run(self, payload: IngestKnowledgebasePayload) -> None:
        logger.info(
            "Starting ingest knowledgebase_id=%s job_id=%s",
            payload.knowledgebase_id,
            payload.job_id,
        )
        try:
            await self._knowledgebase_repository.update_status(
                knowledgebase_id=payload.knowledgebase_id,
                status=KB_STATUS_EXTRACTING,
            )

            documents = await self._extract_source(payload)
            chunks = await asyncio.to_thread(chunk_documents, documents=documents)

            await self._kb_chunk_repository.delete_by_knowledgebase(
                knowledgebase_id=payload.knowledgebase_id,
            )
            await self._kb_chunk_repository.insert_many(
                knowledgebase_id=payload.knowledgebase_id,
                organization_id=payload.organization_id,
                chunks=chunks,
            )
            await self._knowledgebase_repository.update_status(
                knowledgebase_id=payload.knowledgebase_id,
                status=KB_STATUS_CHUNKING,
            )

            await self._knowledgebase_repository.update_status(
                knowledgebase_id=payload.knowledgebase_id,
                status=KB_STATUS_INDEXING,
            )
            index_ref = await asyncio.to_thread(
                self._indexer.index,
                storage_type=payload.storage_type.value,
                organization_id=payload.organization_id,
                knowledgebase_id=payload.knowledgebase_id,
                chunks=chunks,
            )

            await self._knowledgebase_repository.update_status(
                knowledgebase_id=payload.knowledgebase_id,
                status=KB_STATUS_READY,
            )
            await self._job_log_repository.update_status(
                job_id=payload.job_id,
                status=JOB_STATUS_COMPLETED,
            )
            logger.info(
                "Completed ingest knowledgebase_id=%s index_ref=%s",
                payload.knowledgebase_id,
                index_ref,
            )
        except Exception:
            logger.exception(
                "Ingest failed knowledgebase_id=%s job_id=%s",
                payload.knowledgebase_id,
                payload.job_id,
            )
            await self._mark_failed(payload)
            raise

    async def _mark_failed(self, payload: IngestKnowledgebasePayload) -> None:
        try:
            await self._knowledgebase_repository.update_status(
                knowledgebase_id=payload.knowledgebase_id,
                status=KB_STATUS_FAILED,
            )
            await self._job_log_repository.update_status(
                job_id=payload.job_id,
                status=JOB_STATUS_FAILED,
            )
        except Exception:
            logger.exception("Failed to mark ingest as failed for job_id=%s", payload.job_id)

    async def _extract_source(self, payload: IngestKnowledgebasePayload) -> list[SourceDocument]:
        if payload.source_type.value == SOURCE_TYPE_FILE:
            if not payload.s3_key:
                raise ValueError("s3_key is required for file source")
            return await self._extract_from_file(s3_key=payload.s3_key)

        if payload.source_type.value == SOURCE_TYPE_WEBSITE:
            if not payload.website_url or payload.crawl_depth is None:
                raise ValueError("website_url and crawl_depth are required for website source")
            return await asyncio.to_thread(
                scrape_website,
                website_url=payload.website_url,
                crawl_depth=payload.crawl_depth,
            )

        raise ValueError(f"Unsupported source_type: {payload.source_type}")

    async def _extract_from_file(self, *, s3_key: str) -> list[SourceDocument]:
        data = await asyncio.to_thread(self._s3_connector.read_bytes, key=s3_key)
        file_name = os.path.basename(s3_key)
        return await asyncio.to_thread(
            parse_file_bytes,
            data=data,
            file_name=file_name,
        )


def build_knowledgebase_ingest_service() -> KnowledgebaseIngestService:
    db = get_motor_db()
    return KnowledgebaseIngestService(
        knowledgebase_repository=KnowledgebaseRepository(db),
        job_log_repository=JobLogRepository(db),
        kb_chunk_repository=KbChunkRepository(db),
        s3_connector=S3Connector(bucket=settings.s3_bucket, region=settings.aws_region),
        indexer=LlamaIndexPipeline(),
    )
