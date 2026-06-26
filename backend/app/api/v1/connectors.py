from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.di.auth import get_current_user
from app.di.connectors import get_connector_service
from app.domain.models.current_user import CurrentUser
from app.schemas.connector import (
    ConnectorStatus,
    ConnectorType,
    CreateConnectorRequest,
    CreateConnectorResponse,
    GetConnectorResponse,
    ListConnectorsResponse,
    ListConnectorTypesResponse,
    UpdateConnectorRequest,
    UpdateConnectorResponse,
)
from app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["Connectors"])
types_router = APIRouter(prefix="/connector-types", tags=["Connectors"])

ConnectorIdPath = Annotated[str, Path(pattern=r"^[a-fA-F0-9]{24}$")]


@router.post("", response_model=CreateConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    body: CreateConnectorRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> CreateConnectorResponse:
    return await service.create(current_user=current_user, request=body)


@router.get("", response_model=ListConnectorsResponse)
async def list_connectors(
    connector_type: ConnectorType | None = Query(default=None, alias="type"),
    connector_status: ConnectorStatus | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> ListConnectorsResponse:
    return await service.list_by_organization(
        current_user=current_user,
        connector_type=connector_type.value if connector_type else None,
        status=connector_status.value if connector_status else None,
    )


@router.get("/{connector_id}", response_model=GetConnectorResponse)
async def get_connector(
    connector_id: ConnectorIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> GetConnectorResponse:
    return await service.get_by_id(current_user=current_user, connector_id=connector_id)


@router.patch("/{connector_id}", response_model=UpdateConnectorResponse)
async def update_connector(
    connector_id: ConnectorIdPath,
    body: UpdateConnectorRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> UpdateConnectorResponse:
    return await service.update(
        current_user=current_user,
        connector_id=connector_id,
        request=body,
    )


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: ConnectorIdPath,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> Response:
    await service.delete(current_user=current_user, connector_id=connector_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@types_router.get("", response_model=ListConnectorTypesResponse)
async def list_connector_types(
    current_user: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> ListConnectorTypesResponse:
    _ = current_user
    return service.list_connector_types()
