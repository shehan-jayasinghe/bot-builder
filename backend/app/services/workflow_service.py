from typing import Any

from app.domain.constants.workflow_constants import (
    DEFAULT_STARTER_EDGES,
    DEFAULT_STARTER_NODES,
    MAX_WORKFLOWS_PER_ORGANIZATION,
    WORKFLOW_STATUS_DRAFT,
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
        return self._document_to_response(saved)

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        status: str | None = None,
        agent_id: str | None = None,
    ) -> ListWorkflowsResponse:
        documents = await self._workflow_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            status=status,
            agent_id=agent_id,
        )
        items = [self._document_to_list_item(document) for document in documents]
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
        return self._document_to_response(document)

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

        await self._ensure_agent_if_needed(
            request=request,
            organization_id=current_user.organization_id,
        )

        updates = self._build_update_fields(request)
        updated = await self._workflow_repository.update(
            workflow_id=workflow_id,
            organization_id=current_user.organization_id,
            updates=updates,
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

    def _document_to_list_item(self, document: dict[str, Any]) -> WorkflowListItem:
        nodes = document.get("nodes") or []
        return WorkflowListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            agent_id=document.get("agent_id"),
            status=str(document.get("status", WORKFLOW_STATUS_DRAFT)),
            node_count=len(nodes),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    def _document_to_response(self, document: dict[str, Any]) -> WorkflowResponse:
        return WorkflowResponse(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            agent_id=document.get("agent_id"),
            status=str(document.get("status", WORKFLOW_STATUS_DRAFT)),
            nodes=list(document.get("nodes") or []),
            edges=list(document.get("edges") or []),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
