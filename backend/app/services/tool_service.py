from typing import Any

from pydantic import ValidationError

from app.domain.constants.capability_catalog_constants import TOOLS_SECTION
from app.domain.constants.executor_constants import EXECUTOR_CONNECTOR_TYPES
from app.domain.constants.tool_constants import TOOL_STATUS_ACTIVE
from app.domain.models.capability_catalog import (
    get_routing_hint,
    parse_capability_catalog,
    resolve_routing_hint_for_upsert,
    should_sync_catalog_on_agent_change,
)
from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.schemas.tool import (
    CreateToolRequest,
    CreateToolResponse,
    ExecutorName,
    GetToolResponse,
    ListToolsResponse,
    ToolListItem,
    ToolResponse,
    UpdateToolRequest,
    UpdateToolResponse,
)
from app.schemas.tool_config import parse_tool_config
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.connector import ConnectorNotFoundError
from app.shared.exceptions.tool import (
    ToolConnectorTypeMismatchError,
    ToolNameExistsError,
    ToolNotFoundError,
)


class ToolService:
    def __init__(
        self,
        *,
        tool_repository: ToolRepository,
        agent_repository: AgentRepository,
        connector_repository: ConnectorRepository,
    ) -> None:
        self._tool_repository = tool_repository
        self._agent_repository = agent_repository
        self._connector_repository = connector_repository

    async def create(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        request: CreateToolRequest,
    ) -> CreateToolResponse:
        await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)

        existing = await self._tool_repository.find_by_name_for_agent(
            name=request.name,
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if existing is not None:
            raise ToolNameExistsError("Tool name already exists for this agent")

        connector = await self._load_connector(
            connector_id=request.connector_id,
            organization_id=current_user.organization_id,
        )
        self._validate_connector_executor_match(
            executor=request.executor.value,
            connector_type=str(connector["type"]),
        )

        try:
            config = parse_tool_config(request.executor.value, request.config)
        except ValidationError as exc:
            raise ToolConnectorTypeMismatchError(str(exc.errors())) from exc
        except ValueError as exc:
            raise ToolConnectorTypeMismatchError(str(exc)) from exc

        document = {
            "name": request.name,
            "description": request.description,
            "executor": request.executor.value,
            "connector_id": request.connector_id,
            "config": config,
            "status": TOOL_STATUS_ACTIVE,
            "organization_id": current_user.organization_id,
            "agent_id": agent_id,
        }
        saved = await self._tool_repository.create(document=document)
        tool_id = str(saved["_id"])
        pushed = await self._agent_repository.push_tool_id(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            tool_id=tool_id,
        )
        if not pushed:
            raise AgentNotFoundError("Agent not found")
        await self._agent_repository.upsert_capability_catalog_entry(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            section=TOOLS_SECTION,
            resource_id=tool_id,
            routing_hint=request.routing_hint,
        )
        return self._document_to_response(saved, routing_hint=request.routing_hint)

    async def list_by_agent(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        executor: str | None = None,
        status: str | None = None,
    ) -> ListToolsResponse:
        agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        documents = await self._tool_repository.find_all_by_agent(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
            executor=executor,
            status=status,
        )
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        items = [
            self._document_to_list_item(
                document,
                routing_hint=get_routing_hint(catalog, TOOLS_SECTION, str(document["_id"])),
            )
            for document in documents
        ]
        return ListToolsResponse(items=items, total=len(items))

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str | None = None,
        executor: str | None = None,
        status: str | None = None,
    ) -> ListToolsResponse:
        catalog = parse_capability_catalog({})
        if agent_id is not None:
            agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
            catalog = parse_capability_catalog(agent.get("capability_catalog"))

        documents = await self._tool_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            agent_id=agent_id,
            executor=executor,
            status=status,
        )
        items = [
            self._document_to_list_item(
                document,
                routing_hint=(
                    get_routing_hint(catalog, TOOLS_SECTION, str(document["_id"]))
                    if agent_id is not None
                    else None
                ),
            )
            for document in documents
        ]
        return ListToolsResponse(items=items, total=len(items))

    async def update(
        self,
        *,
        current_user: CurrentUser,
        tool_id: str,
        request: UpdateToolRequest,
    ) -> UpdateToolResponse:
        existing = await self._tool_repository.find_by_id_for_organization(
            tool_id=tool_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise ToolNotFoundError("Tool not found")

        agent_id_changed = "agent_id" in request.model_fields_set
        hint_changed = "routing_hint" in request.model_fields_set
        if not agent_id_changed and not hint_changed:
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
                preserved_hint = get_routing_hint(previous_catalog, TOOLS_SECTION, tool_id)

        if agent_id_changed:
            if new_agent_id is not None:
                await self._ensure_agent(agent_id=new_agent_id, organization_id=current_user.organization_id)
                duplicate = await self._tool_repository.find_by_name_for_agent(
                    name=str(existing["name"]),
                    agent_id=new_agent_id,
                    organization_id=current_user.organization_id,
                )
                if duplicate is not None and str(duplicate["_id"]) != tool_id:
                    raise ToolNameExistsError("Tool name already exists for this agent")

            if previous_agent_id and previous_agent_id != new_agent_id:
                await self._agent_repository.pull_tool_id(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    tool_id=tool_id,
                )
                await self._agent_repository.remove_capability_catalog_entry(
                    agent_id=str(previous_agent_id),
                    organization_id=current_user.organization_id,
                    section=TOOLS_SECTION,
                    resource_id=tool_id,
                )

            if new_agent_id is not None and new_agent_id != previous_agent_id:
                pushed = await self._agent_repository.push_tool_id(
                    agent_id=new_agent_id,
                    organization_id=current_user.organization_id,
                    tool_id=tool_id,
                )
                if not pushed:
                    raise AgentNotFoundError("Agent not found")

            updated = await self._tool_repository.update(
                tool_id=tool_id,
                organization_id=current_user.organization_id,
                updates={"agent_id": new_agent_id},
            )
            if updated is None:
                raise ToolNotFoundError("Tool not found")
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
                section=TOOLS_SECTION,
                resource_id=tool_id,
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
            routing_hint = get_routing_hint(catalog, TOOLS_SECTION, tool_id)

        return self._document_to_response(updated, routing_hint=routing_hint)

    async def get_by_id(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        tool_id: str,
    ) -> GetToolResponse:
        agent = await self._ensure_agent(agent_id=agent_id, organization_id=current_user.organization_id)
        document = await self._tool_repository.find_by_id_for_agent(
            tool_id=tool_id,
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if document is None:
            raise ToolNotFoundError("Tool not found")
        catalog = parse_capability_catalog(agent.get("capability_catalog"))
        return self._document_to_response(
            document,
            routing_hint=get_routing_hint(catalog, TOOLS_SECTION, tool_id),
        )

    async def _ensure_agent(self, *, agent_id: str, organization_id: str) -> dict[str, Any]:
        agent = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent is None:
            raise AgentNotFoundError("Agent not found")
        return agent

    async def _load_connector(self, *, connector_id: str, organization_id: str) -> dict[str, Any]:
        connector = await self._connector_repository.find_by_id_for_organization(
            connector_id=connector_id,
            organization_id=organization_id,
        )
        if connector is None:
            raise ConnectorNotFoundError("Connector not found")
        return connector

    @staticmethod
    def _validate_connector_executor_match(*, executor: str, connector_type: str) -> None:
        expected = EXECUTOR_CONNECTOR_TYPES.get(executor)
        if expected is None:
            raise ToolConnectorTypeMismatchError(f"Unsupported executor: {executor}")
        if connector_type != expected:
            raise ToolConnectorTypeMismatchError(
                f"Executor {executor} requires connector type {expected}, got {connector_type}"
            )

    def _document_to_list_item(
        self,
        document: dict[str, Any],
        *,
        routing_hint: str | None = None,
    ) -> ToolListItem:
        return ToolListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=str(document["description"]),
            executor=ExecutorName(document["executor"]),
            connector_id=str(document["connector_id"]),
            config=document.get("config") or {},
            status=str(document.get("status", TOOL_STATUS_ACTIVE)),
            agent_id=document.get("agent_id"),
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
    ) -> ToolResponse:
        return ToolResponse(**self._document_to_list_item(document, routing_hint=routing_hint).model_dump())
