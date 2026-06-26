from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ConnectorType(StrEnum):
    MONGO = "mongo"
    HTTP = "http"


class ConnectorStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class HttpAuthType(StrEnum):
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"


class MongoConnectorConfig(BaseModel):
    uri: str = Field(min_length=1)
    database: str = Field(min_length=1)


class HttpConnectorConfig(BaseModel):
    base_url: str = Field(min_length=1)
    auth_type: HttpAuthType = HttpAuthType.NONE
    auth_token: str | None = None
    auth_username: str | None = None
    auth_password: str | None = None
    api_key_header: str | None = None
    default_headers: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "HttpConnectorConfig":
        if self.auth_type == HttpAuthType.BEARER and not self.auth_token:
            raise ValueError("auth_token is required when auth_type is bearer")
        if self.auth_type == HttpAuthType.API_KEY and not self.auth_token:
            raise ValueError("auth_token is required when auth_type is api_key")
        if self.auth_type == HttpAuthType.BASIC:
            if not self.auth_username or self.auth_password is None:
                raise ValueError("auth_username and auth_password are required when auth_type is basic")
        return self


class CreateConnectorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    type: ConnectorType
    config: dict[str, Any]
    test_connection: bool = False


class UpdateConnectorRequest(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    config: dict[str, Any] | None = None
    status: ConnectorStatus | None = None

    @model_validator(mode="after")
    def validate_not_empty(self) -> "UpdateConnectorRequest":
        if self.description is None and self.config is None and self.status is None:
            raise ValueError("At least one field must be provided")
        return self


class ConnectorResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: ConnectorType
    config: dict[str, Any]
    status: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


CreateConnectorResponse = ConnectorResponse
GetConnectorResponse = ConnectorResponse
UpdateConnectorResponse = ConnectorResponse


class ConnectorListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: ConnectorType
    config: dict[str, Any]
    status: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class ListConnectorsResponse(BaseModel):
    items: list[ConnectorListItem]
    total: int


class ConnectorTypeCatalogItem(BaseModel):
    type: ConnectorType
    label: str
    description: str
    mvp: bool
    config_schema: dict[str, Any]
    compatible_executors: list[str]


class ListConnectorTypesResponse(BaseModel):
    items: list[ConnectorTypeCatalogItem]


def parse_connector_config(connector_type: ConnectorType, config: dict[str, Any]) -> dict[str, Any]:
    if connector_type == ConnectorType.MONGO:
        return MongoConnectorConfig.model_validate(config).model_dump()
    if connector_type == ConnectorType.HTTP:
        return HttpConnectorConfig.model_validate(config).model_dump()
    raise ValueError(f"Unsupported connector type: {connector_type}")
