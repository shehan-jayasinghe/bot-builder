from typing import Any

from app.domain.catalog.connector_type_catalog import get_connector_type_catalog
from app.domain.constants.connector_constants import CONNECTOR_STATUS_ACTIVE
from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.schemas.connector import (
    ConnectorListItem,
    ConnectorResponse,
    ConnectorType,
    ConnectorTypeCatalogItem,
    CreateConnectorRequest,
    ListConnectorsResponse,
    ListConnectorTypesResponse,
    UpdateConnectorRequest,
    parse_connector_config,
)
from app.services.connector_masking import mask_connector_config
from app.services.connector_ping import test_connector_connection
from app.shared.exceptions.connector import (
    ConnectorNameExistsError,
    ConnectorNotFoundError,
)


class ConnectorService:
    def __init__(self, connector_repository: ConnectorRepository) -> None:
        self._connector_repository = connector_repository

    async def create(
        self,
        *,
        current_user: CurrentUser,
        request: CreateConnectorRequest,
    ) -> ConnectorResponse:
        existing = await self._connector_repository.find_by_name_for_organization(
            name=request.name,
            organization_id=current_user.organization_id,
        )
        if existing is not None:
            raise ConnectorNameExistsError("Connector name already exists")

        config = parse_connector_config(request.type, request.config)

        if request.test_connection:
            await test_connector_connection(request.type.value, config)

        document = {
            "name": request.name,
            "description": request.description,
            "type": request.type.value,
            "config": config,
            "status": CONNECTOR_STATUS_ACTIVE,
            "organization_id": current_user.organization_id,
        }
        saved = await self._connector_repository.create(document=document)
        return self._document_to_response(saved)

    async def get_by_id(
        self,
        *,
        current_user: CurrentUser,
        connector_id: str,
    ) -> ConnectorResponse:
        document = await self._connector_repository.find_by_id_for_organization(
            connector_id=connector_id,
            organization_id=current_user.organization_id,
        )
        if document is None:
            raise ConnectorNotFoundError("Connector not found")
        return self._document_to_response(document)

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        connector_type: str | None = None,
        status: str | None = None,
    ) -> ListConnectorsResponse:
        documents = await self._connector_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            connector_type=connector_type,
            status=status,
        )
        items = [self._document_to_list_item(document) for document in documents]
        return ListConnectorsResponse(items=items, total=len(items))

    async def update(
        self,
        *,
        current_user: CurrentUser,
        connector_id: str,
        request: UpdateConnectorRequest,
    ) -> ConnectorResponse:
        existing = await self._connector_repository.find_by_id_for_organization(
            connector_id=connector_id,
            organization_id=current_user.organization_id,
        )
        if existing is None:
            raise ConnectorNotFoundError("Connector not found")

        updates: dict[str, Any] = {}
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status.value
        if request.config is not None:
            connector_type = ConnectorType(existing["type"])
            updates["config"] = parse_connector_config(connector_type, request.config)

        updated = await self._connector_repository.update(
            connector_id=connector_id,
            organization_id=current_user.organization_id,
            updates=updates,
        )
        if updated is None:
            raise ConnectorNotFoundError("Connector not found")
        return self._document_to_response(updated)

    async def delete(
        self,
        *,
        current_user: CurrentUser,
        connector_id: str,
    ) -> None:
        deleted = await self._connector_repository.delete(
            connector_id=connector_id,
            organization_id=current_user.organization_id,
        )
        if not deleted:
            raise ConnectorNotFoundError("Connector not found")

    def list_connector_types(self) -> ListConnectorTypesResponse:
        items = [ConnectorTypeCatalogItem(**item) for item in get_connector_type_catalog()]
        return ListConnectorTypesResponse(items=items)

    def _document_to_list_item(self, document: dict[str, Any]) -> ConnectorListItem:
        connector_type = str(document["type"])
        return ConnectorListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            type=ConnectorType(connector_type),
            config=mask_connector_config(connector_type, document.get("config") or {}),
            status=str(document.get("status", CONNECTOR_STATUS_ACTIVE)),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    def _document_to_response(self, document: dict[str, Any]) -> ConnectorResponse:
        return ConnectorResponse(**self._document_to_list_item(document).model_dump())
