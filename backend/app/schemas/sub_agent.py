import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

_OBJECT_ID_PATTERN = re.compile(r"^[a-fA-F0-9]{24}$")


class SubAgentStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ParameterType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


class SubAgentParameter(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    type: ParameterType
    description: str | None = Field(default=None, max_length=500)
    required: bool = True


class CreateSubAgentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = Field(default=None, max_length=2000)
    instructions: str = Field(min_length=20, max_length=8000)
    tool_ids: list[str] = Field(default_factory=list)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    workflow_ids: list[str] = Field(default_factory=list)
    parameters: list[SubAgentParameter] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_parameter_names(self) -> "CreateSubAgentRequest":
        names = [parameter.name for parameter in self.parameters]
        if len(names) != len(set(names)):
            raise ValueError("Parameter names must be unique")
        return self

    @field_validator("tool_ids", "knowledge_base_ids", "workflow_ids")
    @classmethod
    def validate_object_id_list(cls, values: list[str]) -> list[str]:
        for value in values:
            if not _OBJECT_ID_PATTERN.match(value):
                raise ValueError(f"Invalid ObjectId: {value}")
        return values


class SubAgentResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    instructions: str
    tool_ids: list[str]
    knowledge_base_ids: list[str]
    workflow_ids: list[str]
    parameters: list[SubAgentParameter]
    status: str
    agent_id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


CreateSubAgentResponse = SubAgentResponse
GetSubAgentResponse = SubAgentResponse
UpdateSubAgentResponse = SubAgentResponse


class SubAgentListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    tool_count: int
    knowledge_base_count: int
    workflow_count: int
    parameter_count: int
    agent_id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class ListSubAgentsResponse(BaseModel):
    items: list[SubAgentListItem]
    total: int


class UpdateSubAgentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = Field(default=None, max_length=2000)
    instructions: str | None = Field(default=None, min_length=20, max_length=8000)
    tool_ids: list[str] | None = None
    knowledge_base_ids: list[str] | None = None
    workflow_ids: list[str] | None = None
    parameters: list[SubAgentParameter] | None = None
    status: SubAgentStatus | None = None

    @model_validator(mode="after")
    def validate_not_empty(self) -> "UpdateSubAgentRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self

    @model_validator(mode="after")
    def validate_unique_parameter_names(self) -> "UpdateSubAgentRequest":
        if self.parameters is None:
            return self
        names = [parameter.name for parameter in self.parameters]
        if len(names) != len(set(names)):
            raise ValueError("Parameter names must be unique")
        return self

    @field_validator("tool_ids", "knowledge_base_ids", "workflow_ids")
    @classmethod
    def validate_object_id_list(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        for value in values:
            if not _OBJECT_ID_PATTERN.match(value):
                raise ValueError(f"Invalid ObjectId: {value}")
        return values
