from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.constants.executor_constants import ExecutorName


class ToolStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class CreateToolRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1, max_length=2000)
    executor: ExecutorName
    connector_id: str = Field(pattern=r"^[a-fA-F0-9]{24}$")
    config: dict[str, Any]


class ToolResponse(BaseModel):
    id: str
    name: str
    description: str
    executor: ExecutorName
    connector_id: str
    config: dict[str, Any]
    status: str
    agent_id: str | None = None
    organization_id: str
    created_at: datetime
    updated_at: datetime


CreateToolResponse = ToolResponse
GetToolResponse = ToolResponse


class ToolListItem(BaseModel):
    id: str
    name: str
    description: str
    executor: ExecutorName
    connector_id: str
    config: dict[str, Any]
    status: str
    agent_id: str | None = None
    organization_id: str
    created_at: datetime
    updated_at: datetime


class ListToolsResponse(BaseModel):
    items: list[ToolListItem]
    total: int


class UpdateToolRequest(BaseModel):
    agent_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{24}$")

    @model_validator(mode="after")
    def validate_not_empty(self) -> "UpdateToolRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


UpdateToolResponse = ToolResponse
