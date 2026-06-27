import asyncio
import logging
import os
from typing import Any

from bson import ObjectId
from fastapi import UploadFile

from app.domain.constants.capability_catalog_constants import KNOWLEDGE_BASES_SECTION
from app.domain.constants.knowledgebase_constants import (
    JOB_STATUS_RUNNING,
    KB_STATUS_PENDING,
    SOURCE_TYPE_FILE,
)
from app.domain.models.capability_catalog import (
    get_routing_hint,
    parse_capability_catalog,
    resolve_routing_hint_for_upsert,
    should_sync_catalog_on_agent_change,
)
from app.domain.models.current_user import CurrentUser
from app.infrastructure.connectors.aws.s3_connector import S3Connector
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.job_log_repository import JobLogRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.schemas.knowledgebase import (
    CreateKnowledgebaseRequest,
    CreateKnowledgebaseResponse,
    IngestKnowledgebasePayload,
    KnowledgebaseListItem,
    ListKnowledgebasesResponse,
    SourceType,
    StorageType,
    UpdateKnowledgebaseRequest,
    UpdateKnowledgebaseResponse,
)
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.knowledgebase import KnowledgebaseNotFoundError
from app.workers.tasks.ingest import ingest_knowledgebase

logger = logging.getLogger(__name__)


class KnowledgebaseService:
    def __init__(
        self,
        *,
        knowledgebase_repository: KnowledgebaseRepository,
        job_log_repository: JobLogRepository,
        agent_repository: AgentRepository,
        s3_connector: S3Connector,
    ) -> None:
        self._knowledgebase_repository = knowledgebase_repository
        self._job_log_repository = job_log_repository
        self._agent_repository = agent_repository
        self._s3_connector = s3_connector

    async def create(
        self,
        *,
        current_user: CurrentUser,
        request: CreateKnowledgebaseRequest,
        file: UploadFile | None = None,
    ) -> CreateKnowledgebaseResponse:
        if request.agent_id is not None:
            await self._validate_agent(
                agent_id=request.agent_id,
                organization_id=current_user.organization_id,
            )

        knowledgebase_id = ObjectId()
        organization_id = current_user.organization_id
        s3_key: str | None = None
        s3_uri: str | None = None

        if request.source_type == SourceType.FILE:
            assert file is not None and file.filename
            file_name = os.path.basename(file.filename)
            s3_key = f"{organization_id}/{knowledgebase_id}/{file_name}"
            try:
                await asyncio.to_thread(
                    self._s3_connector.upload_stream,
                    key=s3_key,
                    stream=file.file,
                    content_type=file.content_type,
                )
                s3_uri = self._s3_connector.build_uri(key=s3_key)
            except Exception:
                logger.exception("S3 upload failed for knowledgebase_id=%s", knowledgebase_id)
                raise

        kb_document = self._build_knowledgebase_document(
            request=request,
            organization_id=organization_id,
            s3_key=s3_key,
            s3_uri=s3_uri,
        )

        try:
            saved_kb = await self._knowledgebase_repository.create(
                document=kb_document,
                knowledgebase_id=knowledgebase_id,
            )
        except Exception:
            if s3_key is not None:
                await asyncio.to_thread(self._s3_connector.delete_object, key=s3_key)
            raise

        job_document = {
            "knowledgebase_id": str(knowledgebase_id),
            "organization_id": organization_id,
            "storage_type": request.storage_type.value,
            "status": JOB_STATUS_RUNNING,
        }
        saved_job = await self._job_log_repository.create(document=job_document)

        kb_id = str(knowledgebase_id)
        if request.agent_id is not None:
            pushed = await self._agent_repository.push_knowledge_base_id(
                agent_id=request.agent_id,
                organization_id=organization_id,
                knowledgebase_id=kb_id,
            )
            if not pushed:
                raise AgentNotFoundError("Agent not found")
            await self._agent_repository.upsert_capability_catalog_entry(
                agent_id=request.agent_id,
                organization_id=organization_id,
                section=KNOWLEDGE_BASES_SECTION,
                resource_id=kb_id,
                routing_hint=request.routing_hint,
            )

        self._enqueue_ingest(
            IngestKnowledgebasePayload(
                knowledgebase_id=str(knowledgebase_id),
                job_id=str(saved_job["_id"]),
                organization_id=organization_id,
                source_type=request.source_type,
                storage_type=request.storage_type,
                website_url=kb_document.get("website_url"),
                crawl_depth=kb_document.get("crawl_depth"),
                agent_id=request.agent_id,
                s3_key=s3_key,
            )
        )

        return self._to_response(saved_kb, saved_job, routing_hint=request.routing_hint)

    async def list_by_agent(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        status: str | None = None,
    ) -> ListKnowledgebasesResponse:
        agent = await self._validate_agent(agent_id=agent_id, organization_id=current_user.organization_id)

        documents = await self._knowledgebase_repository.find_all_by_agent(
            organization_id=current_user.organization_id,
            agent_id=agent_id,
            status=status,
        )
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        items = [
            self._document_to_list_item(
                document,
                routing_hint=get_routing_hint(catalog, KNOWLEDGE_BASES_SECTION, str(document["_id"])),
            )
            for document in documents
        ]
        return ListKnowledgebasesResponse(items=items, total=len(items))

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str | None = None,
        status: str | None = None,
    ) -> ListKnowledgebasesResponse:
        catalog = parse_capability_catalog({})
        if agent_id is not None:
            agent = await self._validate_agent(agent_id=agent_id, organization_id=current_user.organization_id)
            catalog = parse_capability_catalog(agent.get("capability_catalog"))

        documents = await self._knowledgebase_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            agent_id=agent_id,
            status=status,
        )
        items = [
            self._document_to_list_item(
                document,
                routing_hint=(
                    get_routing_hint(catalog, KNOWLEDGE_BASES_SECTION, str(document["_id"]))
                    if agent_id is not None
                    else None
                ),
            )
            for document in documents
        ]
        return ListKnowledgebasesResponse(items=items, total=len(items))

    async def update(
        self,
        *,
        current_user: CurrentUser,
        knowledgebase_id: str,
        request: UpdateKnowledgebaseRequest,
    ) -> UpdateKnowledgebaseResponse:
        existing = await self._knowledgebase_repository.find_by_id_for_organization(
            knowledgebase_id=knowledgebase_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise KnowledgebaseNotFoundError("Knowledge base not found")

        agent_id_changed = "agent_id" in request.model_fields_set
        hint_changed = "routing_hint" in request.model_fields_set
        if not agent_id_changed and not hint_changed:
            return self._document_to_update_response(existing)

        previous_agent_id = existing.get("agent_id")
        new_agent_id = request.agent_id if agent_id_changed else previous_agent_id
        preserved_hint: str | None = None
        if (
            agent_id_changed
            and previous_agent_id
            and previous_agent_id != new_agent_id
            and not hint_changed
        ):
            previous_agent = await self._agent_repository.find_by_id_for_organization(
                agent_id=str(previous_agent_id),
                organization_id=current_user.organization_id,
            )
            if previous_agent is not None:
                previous_catalog = parse_capability_catalog(previous_agent.get("capability_catalog"))
                preserved_hint = get_routing_hint(previous_catalog, KNOWLEDGE_BASES_SECTION, knowledgebase_id)

        if agent_id_changed:
            if new_agent_id is not None:
                await self._validate_agent(
                    agent_id=new_agent_id,
                    organization_id=current_user.organization_id,
                )

            if previous_agent_id and previous_agent_id != new_agent_id:
                await self._agent_repository.pull_knowledge_base_id(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    knowledgebase_id=knowledgebase_id,
                )
                await self._agent_repository.remove_capability_catalog_entry(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    section=KNOWLEDGE_BASES_SECTION,
                    resource_id=knowledgebase_id,
                )

            if new_agent_id is not None and new_agent_id != previous_agent_id:
                pushed = await self._agent_repository.push_knowledge_base_id(
                    agent_id=new_agent_id,
                    organization_id=current_user.organization_id,
                    knowledgebase_id=knowledgebase_id,
                )
                if not pushed:
                    raise AgentNotFoundError("Agent not found")

            updated = await self._knowledgebase_repository.update(
                knowledgebase_id=knowledgebase_id,
                organization_id=current_user.organization_id,
                updates={"agent_id": new_agent_id},
            )
            if updated is None:
                raise KnowledgebaseNotFoundError("Knowledge base not found")
        else:
            updated = existing

        if should_sync_catalog_on_agent_change(
            agent_id_changed=agent_id_changed,
            hint_changed=hint_changed,
            previous_agent_id=str(previous_agent_id) if previous_agent_id else None,
            new_agent_id=str(new_agent_id) if new_agent_id else None,
        ):
            await self._agent_repository.upsert_capability_catalog_entry(
                agent_id=str(new_agent_id),
                organization_id=current_user.organization_id,
                section=KNOWLEDGE_BASES_SECTION,
                resource_id=knowledgebase_id,
                routing_hint=resolve_routing_hint_for_upsert(
                    hint_changed=hint_changed,
                    request_routing_hint=request.routing_hint,
                    preserved_routing_hint=preserved_hint,
                ),
            )

        routing_hint: str | None = None
        if new_agent_id is not None:
            agent_doc = await self._agent_repository.find_by_id_for_organization(
                agent_id=str(new_agent_id),
                organization_id=current_user.organization_id,
            )
            catalog = parse_capability_catalog((agent_doc or {}).get("capability_catalog"))
            routing_hint = get_routing_hint(catalog, KNOWLEDGE_BASES_SECTION, knowledgebase_id)

        return self._document_to_update_response(updated, routing_hint=routing_hint)

    @staticmethod
    def _document_to_list_item(
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> KnowledgebaseListItem:
        return KnowledgebaseListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            source_type=SourceType(document["source_type"]),
            storage_type=StorageType(document["storage_type"]),
            website_url=document.get("website_url"),
            crawl_depth=document.get("crawl_depth"),
            agent_id=document.get("agent_id"),
            routing_hint=routing_hint,
            status=str(document["status"]),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
        )

    @staticmethod
    def _document_to_update_response(
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> UpdateKnowledgebaseResponse:
        return UpdateKnowledgebaseResponse(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            source_type=SourceType(document["source_type"]),
            storage_type=StorageType(document["storage_type"]),
            website_url=document.get("website_url"),
            crawl_depth=document.get("crawl_depth"),
            agent_id=document.get("agent_id"),
            routing_hint=routing_hint,
            status=str(document["status"]),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    @staticmethod
    def _enqueue_ingest(payload: IngestKnowledgebasePayload) -> None:
        ingest_knowledgebase.delay(payload.to_task_dict())

    async def _validate_agent(self, *, agent_id: str, organization_id: str) -> dict[str, Any]:
        agent = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent is None:
            raise AgentNotFoundError("Agent not found")
        return agent

    @staticmethod
    def _build_knowledgebase_document(
        *,
        request: CreateKnowledgebaseRequest,
        organization_id: str,
        s3_key: str | None,
        s3_uri: str | None,
    ) -> dict[str, Any]:
        document: dict[str, Any] = {
            "name": request.name,
            "description": request.description,
            "organization_id": organization_id,
            "source_type": request.source_type.value,
            "storage_type": request.storage_type.value,
            "status": KB_STATUS_PENDING,
            "s3_key": s3_key,
            "s3_uri": s3_uri,
            "agent_id": request.agent_id,
        }

        if request.source_type == SOURCE_TYPE_FILE:
            document["website_url"] = None
            document["crawl_depth"] = None
        else:
            document["website_url"] = str(request.website_url)
            document["crawl_depth"] = request.crawl_depth

        return document

    @staticmethod
    def _to_response(
        kb_document: dict[str, Any],
        job_document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> CreateKnowledgebaseResponse:
        return CreateKnowledgebaseResponse(
            id=str(kb_document["_id"]),
            name=str(kb_document["name"]),
            description=kb_document.get("description"),
            organization_id=str(kb_document["organization_id"]),
            source_type=SourceType(kb_document["source_type"]),
            storage_type=StorageType(kb_document["storage_type"]),
            website_url=kb_document.get("website_url"),
            crawl_depth=kb_document.get("crawl_depth"),
            agent_id=kb_document.get("agent_id"),
            routing_hint=routing_hint,
            status=str(kb_document["status"]),
            job_id=str(job_document["_id"]),
            job_status=str(job_document["status"]),
            created_at=kb_document["created_at"],
        )
