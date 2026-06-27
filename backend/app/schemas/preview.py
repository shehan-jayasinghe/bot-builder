from enum import StrEnum

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
