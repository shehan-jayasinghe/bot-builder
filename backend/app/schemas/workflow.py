from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class WorkflowNode(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    position: dict[str, Any]
    data: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)


class CreateWorkflowRequest(BaseModel):
    name: str = Field(default="Welcome", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    agent_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{24}$")
    nodes: list[WorkflowNode] | None = None
    edges: list[WorkflowEdge] | None = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    agent_id: str | None = None
    status: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    organization_id: str
    created_at: datetime
    updated_at: datetime


CreateWorkflowResponse = WorkflowResponse
