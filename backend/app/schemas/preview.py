from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RuntimeGraphNodeType(StrEnum):
    ORCHESTRATOR = "orchestrator"
    TOOL = "tool"
    WORKFLOW = "workflow"
    SUB_AGENT = "sub_agent"
    KNOWLEDGE_BASE = "knowledge_base"


class RuntimeGraphEdgeKind(StrEnum):
    TOOL = "tool"
    WORKFLOW = "workflow"
    SUB_AGENT = "sub_agent"
    KNOWLEDGE_BASE = "knowledge_base"


class RuntimeGraphOrchestrator(BaseModel):
    id: str
    name: str
    kind: str = "orchestrator"
    status: str | None = None
    description: str | None = None


class RuntimeGraphNode(BaseModel):
    id: str
    type: RuntimeGraphNodeType
    label: str
    description: str | None = None


class RuntimeGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    kind: RuntimeGraphEdgeKind


class RuntimeGraphResponse(BaseModel):
    agent_id: str
    organization_id: str
    orchestrator: RuntimeGraphOrchestrator
    nodes: list[RuntimeGraphNode] = Field(default_factory=list)
    edges: list[RuntimeGraphEdge] = Field(default_factory=list)


class PreviewTraceEvent(BaseModel):
    type: str
    at: str
    data: dict[str, Any] = Field(default_factory=dict)


class PreviewTraceTurn(BaseModel):
    turn_id: str
    started_at: str
    events: list[PreviewTraceEvent] = Field(default_factory=list)
    routing_decision: dict[str, Any] | None = None


class PreviewTraceResponse(BaseModel):
    agent_id: str
    sender_id: str
    source: str | None = None
    turns: list[PreviewTraceTurn] = Field(default_factory=list)
