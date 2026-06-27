from typing import Any

from app.domain.constants.capability_catalog_constants import SUB_AGENTS_SECTION
from app.domain.constants.sub_agent_constants import (
    MAX_SUB_AGENTS_PER_AGENT,
    SUB_AGENT_STATUS_ACTIVE,
)
from app.domain.models.capability_catalog import get_routing_hint, parse_capability_catalog
from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.sub_agent_repository import SubAgentRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.schemas.sub_agent import (
    CreateSubAgentRequest,
    CreateSubAgentResponse,
    GetSubAgentResponse,
    ListSubAgentsResponse,
    SubAgentListItem,
    SubAgentParameter,
    SubAgentResponse,
    UpdateSubAgentRequest,
    UpdateSubAgentResponse,
)
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.sub_agent import (
    SubAgentInvalidCapabilityError,
    SubAgentLimitReachedError,
    SubAgentNameExistsError,
    SubAgentNotFoundError,
)


class SubAgentService:
    def __init__(
        self,
        *,
        sub_agent_repository: SubAgentRepository,
        agent_repository: AgentRepository,
        tool_repository: ToolRepository,
        knowledgebase_repository: KnowledgebaseRepository,
        workflow_repository: WorkflowRepository,
    ) -> None:
        self._sub_agent_repository = sub_agent_repository
        self._agent_repository = agent_repository
        self._tool_repository = tool_repository
        self._knowledgebase_repository = knowledgebase_repository
        self._workflow_repository = workflow_repository

    async def create(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        request: CreateSubAgentRequest,
    ) -> CreateSubAgentResponse:
        await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)

        count = await self._sub_agent_repository.count_by_agent(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if count >= MAX_SUB_AGENTS_PER_AGENT:
            raise SubAgentLimitReachedError(
                f"Sub-agent limit reached ({MAX_SUB_AGENTS_PER_AGENT})"
            )

        existing = await self._sub_agent_repository.find_by_name_for_agent(
            name=request.name,
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if existing is not None:
            raise SubAgentNameExistsError("Sub-agent name already exists for this agent")

        await self._validate_capabilities(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            tool_ids=request.tool_ids,
            knowledge_base_ids=request.knowledge_base_ids,
            workflow_ids=request.workflow_ids,
        )

        document = {
            "name": request.name,
            "description": request.description,
            "instructions": request.instructions,
            "tool_ids": request.tool_ids,
            "knowledge_base_ids": request.knowledge_base_ids,
            "workflow_ids": request.workflow_ids,
            "parameters": [parameter.model_dump() for parameter in request.parameters],
            "status": SUB_AGENT_STATUS_ACTIVE,
            "agent_id": agent_id,
            "organization_id": current_user.organization_id,
        }
        saved = await self._sub_agent_repository.create(document=document)
        sub_agent_id = str(saved["_id"])
        pushed = await self._agent_repository.push_sub_agent_id(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            sub_agent_id=sub_agent_id,
        )
        if not pushed:
            raise AgentNotFoundError("Agent not found")
        await self._agent_repository.upsert_capability_catalog_entry(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            section=SUB_AGENTS_SECTION,
            resource_id=sub_agent_id,
            routing_hint=request.routing_hint,
        )
        return self._document_to_response(saved, routing_hint=request.routing_hint)

    async def list_by_agent(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        status: str | None = None,
    ) -> ListSubAgentsResponse:
        agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        documents = await self._sub_agent_repository.find_all_by_agent(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            status=status,
        )
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        items = [
            self._document_to_list_item(
                document,
                routing_hint=get_routing_hint(catalog, SUB_AGENTS_SECTION, str(document["_id"])),
            )
            for document in documents
        ]
        return ListSubAgentsResponse(items=items, total=len(items))

    async def get_by_id(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        sub_agent_id: str,
    ) -> GetSubAgentResponse:
        agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        document = await self._sub_agent_repository.find_by_id_for_agent(
            sub_agent_id=sub_agent_id,
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if document is None:
            raise SubAgentNotFoundError("Sub-agent not found")
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        return self._document_to_response(
            document,
            routing_hint=get_routing_hint(catalog, SUB_AGENTS_SECTION, sub_agent_id),
        )

    async def update(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        sub_agent_id: str,
        request: UpdateSubAgentRequest,
    ) -> UpdateSubAgentResponse:
        await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        existing = await self._sub_agent_repository.find_by_id_for_agent(
            sub_agent_id=sub_agent_id,
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise SubAgentNotFoundError("Sub-agent not found")

        if "name" in request.model_fields_set and request.name is not None:
            duplicate = await self._sub_agent_repository.find_by_name_for_agent(
                name=request.name,
                agent_id=agent_id,
                organization_id=current_user.organization_id,
                exclude_sub_agent_id=sub_agent_id,
            )
            if duplicate is not None:
                raise SubAgentNameExistsError("Sub-agent name already exists for this agent")

        tool_ids = request.tool_ids if "tool_ids" in request.model_fields_set else None
        knowledge_base_ids = (
            request.knowledge_base_ids if "knowledge_base_ids" in request.model_fields_set else None
        )
        workflow_ids = request.workflow_ids if "workflow_ids" in request.model_fields_set else None
        if tool_ids is not None or knowledge_base_ids is not None or workflow_ids is not None:
            await self._validate_capabilities(
                agent_id=agent_id,
                organization_id=current_user.organization_id,
                tool_ids=tool_ids if tool_ids is not None else list(existing.get("tool_ids") or []),
                knowledge_base_ids=(
                    knowledge_base_ids
                    if knowledge_base_ids is not None
                    else list(existing.get("knowledge_base_ids") or [])
                ),
                workflow_ids=(
                    workflow_ids if workflow_ids is not None else list(existing.get("workflow_ids") or [])
                ),
            )

        updates = self._build_update_fields(request)
        if updates:
            updated = await self._sub_agent_repository.update(
                sub_agent_id=sub_agent_id,
                agent_id=agent_id,
                organization_id=current_user.organization_id,
                updates=updates,
            )
            if updated is None:
                raise SubAgentNotFoundError("Sub-agent not found")
        else:
            updated = existing

        if "routing_hint" in request.model_fields_set:
            await self._agent_repository.upsert_capability_catalog_entry(
                agent_id=agent_id,
                organization_id=current_user.organization_id,
                section=SUB_AGENTS_SECTION,
                resource_id=sub_agent_id,
                routing_hint=request.routing_hint,
            )

        agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        return self._document_to_response(
            updated,
            routing_hint=get_routing_hint(catalog, SUB_AGENTS_SECTION, sub_agent_id),
        )

    async def _ensure_agent(self, *, agent_id: str, organization_id: str) -> dict[str, Any]:
        agent = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent is None:
            raise AgentNotFoundError("Agent not found")
        return agent

    async def _validate_capabilities(
        self,
        *,
        agent_id: str,
        organization_id: str,
        tool_ids: list[str],
        knowledge_base_ids: list[str],
        workflow_ids: list[str],
    ) -> None:
        for tool_id in tool_ids:
            tool = await self._tool_repository.find_by_id_for_agent(
                tool_id=tool_id,
                agent_id=agent_id,
                organization_id=organization_id,
            )
            if tool is None:
                raise SubAgentInvalidCapabilityError(
                    f"Tool {tool_id} is not attached to this agent"
                )

        for knowledgebase_id in knowledge_base_ids:
            kb = await self._knowledgebase_repository.find_by_id_for_organization(
                knowledgebase_id=knowledgebase_id,
                organization_id=organization_id,
            )
            if kb is None or kb.get("agent_id") != agent_id:
                raise SubAgentInvalidCapabilityError(
                    f"Knowledge base {knowledgebase_id} is not attached to this agent"
                )

        for workflow_id in workflow_ids:
            workflow = await self._workflow_repository.find_by_id_for_organization(
                workflow_id=workflow_id,
                organization_id=organization_id,
            )
            if workflow is None or workflow.get("agent_id") != agent_id:
                raise SubAgentInvalidCapabilityError(
                    f"Workflow {workflow_id} is not attached to this agent"
                )

    def _build_update_fields(self, request: UpdateSubAgentRequest) -> dict[str, Any]:
        updates: dict[str, Any] = {}

        if "name" in request.model_fields_set and request.name is not None:
            updates["name"] = request.name
        if "description" in request.model_fields_set:
            updates["description"] = request.description
        if "instructions" in request.model_fields_set and request.instructions is not None:
            updates["instructions"] = request.instructions
        if "tool_ids" in request.model_fields_set and request.tool_ids is not None:
            updates["tool_ids"] = request.tool_ids
        if "knowledge_base_ids" in request.model_fields_set and request.knowledge_base_ids is not None:
            updates["knowledge_base_ids"] = request.knowledge_base_ids
        if "workflow_ids" in request.model_fields_set and request.workflow_ids is not None:
            updates["workflow_ids"] = request.workflow_ids
        if "parameters" in request.model_fields_set and request.parameters is not None:
            updates["parameters"] = [parameter.model_dump() for parameter in request.parameters]
        if "status" in request.model_fields_set and request.status is not None:
            updates["status"] = request.status.value

        return updates

    def _document_to_list_item(
        self,
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> SubAgentListItem:
        tool_ids = list(document.get("tool_ids") or [])
        knowledge_base_ids = list(document.get("knowledge_base_ids") or [])
        workflow_ids = list(document.get("workflow_ids") or [])
        parameters = list(document.get("parameters") or [])
        return SubAgentListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            status=str(document.get("status", SUB_AGENT_STATUS_ACTIVE)),
            tool_count=len(tool_ids),
            knowledge_base_count=len(knowledge_base_ids),
            workflow_count=len(workflow_ids),
            parameter_count=len(parameters),
            agent_id=str(document["agent_id"]),
            organization_id=str(document["organization_id"]),
            routing_hint=routing_hint,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    def _document_to_response(
        self,
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> SubAgentResponse:
        parameters = [
            SubAgentParameter(**parameter) for parameter in (document.get("parameters") or [])
        ]
        return SubAgentResponse(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            instructions=str(document["instructions"]),
            tool_ids=[str(tool_id) for tool_id in (document.get("tool_ids") or [])],
            knowledge_base_ids=[
                str(kb_id) for kb_id in (document.get("knowledge_base_ids") or [])
            ],
            workflow_ids=[str(wf_id) for wf_id in (document.get("workflow_ids") or [])],
            parameters=parameters,
            status=str(document.get("status", SUB_AGENT_STATUS_ACTIVE)),
            agent_id=str(document["agent_id"]),
            organization_id=str(document["organization_id"]),
            routing_hint=routing_hint,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
