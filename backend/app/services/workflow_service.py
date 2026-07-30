from typing import Any

from app.domain.constants.capability_catalog_constants import WORKFLOWS_SECTION
from app.domain.constants.workflow_constants import (
    DEFAULT_STARTER_EDGES,
    DEFAULT_STARTER_NODES,
    MAX_WORKFLOWS_PER_ORGANIZATION,
    WORKFLOW_STATUS_DRAFT,
    WORKFLOW_STATUS_PUBLISHED,
)
from app.domain.models.capability_catalog import (
    get_routing_hint,
    parse_capability_catalog,
    resolve_routing_hint_for_upsert,
    should_sync_catalog_on_agent_change,
)
from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.schemas.workflow import (
    CreateWorkflowRequest,
    CreateWorkflowResponse,
    GetWorkflowResponse,
    ListWorkflowsResponse,
    UpdateWorkflowRequest,
    UpdateWorkflowResponse,
    WorkflowListItem,
    WorkflowResponse,
)
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.workflow import WorkflowLimitReachedError, WorkflowNotFoundError
from app.services.workflow_validator import validate_workflow_for_publish


class WorkflowService:
    def __init__(
        self,
        *,
        workflow_repository: WorkflowRepository,
        agent_repository: AgentRepository,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._agent_repository = agent_repository

    async def create(
        self,
        *,
        current_user: CurrentUser,
        request: CreateWorkflowRequest,
    ) -> CreateWorkflowResponse:
        if request.agent_id is not None:
            agent = await self._agent_repository.find_by_id_for_organization(
                agent_id=request.agent_id,
                organization_id=current_user.organization_id,
            )
            if agent is None:
                raise AgentNotFoundError("Agent not found")

        count = await self._workflow_repository.count_by_organization(
            organization_id=current_user.organization_id,
        )
        if count >= MAX_WORKFLOWS_PER_ORGANIZATION:
            raise WorkflowLimitReachedError(
                f"Organization workflow limit reached ({MAX_WORKFLOWS_PER_ORGANIZATION})"
            )

        nodes = (
            [node.model_dump() for node in request.nodes]
            if request.nodes is not None
            else list(DEFAULT_STARTER_NODES)
        )
        edges = (
            [edge.model_dump() for edge in request.edges]
            if request.edges is not None
            else list(DEFAULT_STARTER_EDGES)
        )

        document = {
            "name": request.name,
            "description": request.description,
            "agent_id": request.agent_id,
            "status": WORKFLOW_STATUS_DRAFT,
            "nodes": nodes,
            "edges": edges,
            "organization_id": current_user.organization_id,
        }
        saved = await self._workflow_repository.create(document=document)
        workflow_id = str(saved["_id"])
        if request.agent_id is not None:
            pushed = await self._agent_repository.push_workflow_id(
                agent_id=request.agent_id,
                organization_id=current_user.organization_id,
                workflow_id=workflow_id,
            )
            if not pushed:
                raise AgentNotFoundError("Agent not found")
            await self._agent_repository.upsert_capability_catalog_entry(
                agent_id=request.agent_id,
                organization_id=current_user.organization_id,
                section=WORKFLOWS_SECTION,
                resource_id=workflow_id,
                routing_hint=request.routing_hint,
            )
        return self._document_to_response(saved, routing_hint=request.routing_hint)

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        status: str | None = None,
        agent_id: str | None = None,
    ) -> ListWorkflowsResponse:
        catalog = parse_capability_catalog({})
        if agent_id is not None:
            agent = await self._agent_repository.find_by_id_for_organization(
                agent_id=agent_id,
                organization_id=current_user.organization_id,
            )
            if agent is None:
                raise AgentNotFoundError("Agent not found")
            catalog = parse_capability_catalog(agent.get("capability_catalog"))

        documents = await self._workflow_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            status=status,
            agent_id=agent_id,
        )
        items = [
            self._document_to_list_item(
                document,
                routing_hint=(
                    get_routing_hint(catalog, WORKFLOWS_SECTION, str(document["_id"]))
                    if agent_id is not None
                    else None
                ),
            )
            for document in documents
        ]
        return ListWorkflowsResponse(items=items, total=len(items))

    async def get_by_id(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
    ) -> GetWorkflowResponse:
        document = await self._workflow_repository.find_by_id_for_organization(
            workflow_id=workflow_id,
            organization_id=current_user.organization_id,
        )
        if document is None:
            raise WorkflowNotFoundError("Workflow not found")
        routing_hint: str | None = None
        agent_id = document.get("agent_id")
        if agent_id:
            agent_doc = await self._agent_repository.find_by_id_for_organization(
                agent_id=str(agent_id),
                organization_id=current_user.organization_id,
            )
            catalog = parse_capability_catalog((agent_doc or {}).get("capability_catalog"))
            routing_hint = get_routing_hint(catalog, WORKFLOWS_SECTION, workflow_id)
        return self._document_to_response(document, routing_hint=routing_hint)

    async def update(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
        request: UpdateWorkflowRequest,
    ) -> UpdateWorkflowResponse:
        existing = await self._workflow_repository.find_by_id_for_organization(
            workflow_id=workflow_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise WorkflowNotFoundError("Workflow not found")

        agent_id_changed = "agent_id" in request.model_fields_set
        hint_changed = "routing_hint" in request.model_fields_set
        content_fields = {"name", "description", "nodes", "edges"}
        has_content_updates = bool(content_fields.intersection(request.model_fields_set))

        if not agent_id_changed and not hint_changed and not has_content_updates:
            return self._document_to_response(existing)

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
                preserved_hint = get_routing_hint(previous_catalog, WORKFLOWS_SECTION, workflow_id)

        if agent_id_changed:
            if new_agent_id is not None:
                await self._ensure_agent_if_needed(
                    request=request,
                    organization_id=current_user.organization_id,
                )

            if previous_agent_id and previous_agent_id != new_agent_id:
                await self._agent_repository.pull_workflow_id(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    workflow_id=workflow_id,
                )
                await self._agent_repository.remove_capability_catalog_entry(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    section=WORKFLOWS_SECTION,
                    resource_id=workflow_id,
                )

            if new_agent_id is not None and new_agent_id != previous_agent_id:
                pushed = await self._agent_repository.push_workflow_id(
                    agent_id=new_agent_id,
                    organization_id=current_user.organization_id,
                    workflow_id=workflow_id,
                )
                if not pushed:
                    raise AgentNotFoundError("Agent not found")

        updates = self._build_update_fields(request)
        if agent_id_changed:
            updates["agent_id"] = new_agent_id
        if updates:
            self._maybe_revert_published_to_draft(existing=existing, updates=updates)
            updated = await self._workflow_repository.update(
                workflow_id=workflow_id,
                organization_id=current_user.organization_id,
                updates=updates,
            )
            if updated is None:
                raise WorkflowNotFoundError("Workflow not found")
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
                section=WORKFLOWS_SECTION,
                resource_id=workflow_id,
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
            routing_hint = get_routing_hint(catalog, WORKFLOWS_SECTION, workflow_id)

        return self._document_to_response(updated, routing_hint=routing_hint)

    async def publish(
        self,
        *,
        current_user: CurrentUser,
        workflow_id: str,
    ) -> UpdateWorkflowResponse:
        existing = await self._workflow_repository.find_by_id_for_organization(
            workflow_id=workflow_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise WorkflowNotFoundError("Workflow not found")

        nodes = list(existing.get("nodes") or [])
        edges = list(existing.get("edges") or [])
        validate_workflow_for_publish(nodes=nodes, edges=edges)

        updated = await self._workflow_repository.update(
            workflow_id=workflow_id,
            organization_id=current_user.organization_id,
            updates={"status": WORKFLOW_STATUS_PUBLISHED},
        )
        if updated is None:
            raise WorkflowNotFoundError("Workflow not found")
        return self._document_to_response(updated)

    def _build_update_fields(self, request: UpdateWorkflowRequest) -> dict[str, Any]:
        updates: dict[str, Any] = {}

        if "name" in request.model_fields_set and request.name is not None:
            updates["name"] = request.name
        if "description" in request.model_fields_set:
            updates["description"] = request.description
        if "agent_id" in request.model_fields_set:
            updates["agent_id"] = request.agent_id
        if "nodes" in request.model_fields_set and request.nodes is not None:
            updates["nodes"] = [node.model_dump() for node in request.nodes]
        if "edges" in request.model_fields_set and request.edges is not None:
            updates["edges"] = [edge.model_dump() for edge in request.edges]

        return updates

    def _maybe_revert_published_to_draft(
        self,
        *,
        existing: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        if existing.get("status") != WORKFLOW_STATUS_PUBLISHED:
            return
        content_fields = {"name", "description", "nodes", "edges"}
        if content_fields.intersection(updates):
            updates["status"] = WORKFLOW_STATUS_DRAFT

    async def _ensure_agent_if_needed(
        self,
        *,
        request: UpdateWorkflowRequest,
        organization_id: str,
    ) -> None:
        if "agent_id" not in request.model_fields_set or request.agent_id is None:
            return
        agent = await self._agent_repository.find_by_id_for_organization(
            agent_id=request.agent_id,
            organization_id=organization_id,
        )
        if agent is None:
            raise AgentNotFoundError("Agent not found")

    def _document_to_list_item(
        self,
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> WorkflowListItem:
        nodes = document.get("nodes") or []
        return WorkflowListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            agent_id=document.get("agent_id"),
            routing_hint=routing_hint,
            status=str(document.get("status", WORKFLOW_STATUS_DRAFT)),
            node_count=len(nodes),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    def _document_to_response(
        self,
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> WorkflowResponse:
        return WorkflowResponse(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            agent_id=document.get("agent_id"),
            routing_hint=routing_hint,
            status=str(document.get("status", WORKFLOW_STATUS_DRAFT)),
            nodes=list(document.get("nodes") or []),
            edges=list(document.get("edges") or []),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
