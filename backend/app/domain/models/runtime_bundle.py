from typing import Any

from pydantic import BaseModel, Field

from app.domain.models.assistant import LLMConfig
from app.domain.models.capability_catalog import CapabilityCatalog


class RuntimeTool(BaseModel):
    id: str
    name: str
    description: str
    executor: str
    connector_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    status: str


class RuntimeKnowledgeBase(BaseModel):
    id: str
    name: str
    description: str | None = None
    storage_type: str
    status: str


class RuntimeWorkflow(BaseModel):
    id: str
    name: str
    description: str | None = None
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    status: str


class RuntimeSubAgentParameter(BaseModel):
    name: str
    type: str
    description: str | None = None
    required: bool = True


class RuntimeSubAgent(BaseModel):
    id: str
    name: str
    description: str | None = None
    instructions: str
    parameters: list[RuntimeSubAgentParameter] = Field(default_factory=list)
    tools: list[RuntimeTool] = Field(default_factory=list)
    knowledge_bases: list[RuntimeKnowledgeBase] = Field(default_factory=list)
    workflows: list[RuntimeWorkflow] = Field(default_factory=list)
    status: str


class RuntimeOrchestrator(BaseModel):
    id: str
    name: str
    system_prompt: str
    personality: str | None = None
    tone: str | None = None
    llm_config: LLMConfig | None = None
    temperature: float = 0.7
    max_output_tokens: int = 1024
    guardrails: list[dict[str, Any]] = Field(default_factory=list)
    tools: list[RuntimeTool] = Field(default_factory=list)
    knowledge_bases: list[RuntimeKnowledgeBase] = Field(default_factory=list)
    workflows: list[RuntimeWorkflow] = Field(default_factory=list)
    sub_agents: list[RuntimeSubAgent] = Field(default_factory=list)

    def find_sub_agent_by_name(self, name: str) -> RuntimeSubAgent | None:
        normalized = name.strip().lower()
        for sub_agent in self.sub_agents:
            if sub_agent.name == normalized or sub_agent.name == name:
                return sub_agent
        return None

    def find_sub_agent_by_id(self, sub_agent_id: str) -> RuntimeSubAgent | None:
        for sub_agent in self.sub_agents:
            if sub_agent.id == sub_agent_id:
                return sub_agent
        return None

    def find_workflow_by_id(self, workflow_id: str) -> RuntimeWorkflow | None:
        for workflow in self.workflows:
            if workflow.id == workflow_id:
                return workflow
        return None

    def find_workflow_by_name(self, name: str) -> RuntimeWorkflow | None:
        normalized = name.strip().lower()
        for workflow in self.workflows:
            if workflow.name.strip().lower() == normalized or workflow.name == name:
                return workflow
        return None

    def build_system_prompt(self, *, rag_context: str | None = None) -> str:
        parts = [self.system_prompt]
        if self.personality:
            parts.append(f"Personality: {self.personality}")
        if self.tone:
            parts.append(f"Tone: {self.tone}")
        if rag_context:
            parts.append("## Retrieved context\n" + rag_context)
        return "\n\n".join(parts)


class RuntimeBundle(BaseModel):
    orchestrator: RuntimeOrchestrator
    organization_id: str
    capability_catalog: CapabilityCatalog = Field(default_factory=CapabilityCatalog)

    def all_runtime_tools(self) -> list[RuntimeTool]:
        tools = list(self.orchestrator.tools)
        for sub_agent in self.orchestrator.sub_agents:
            tools.extend(sub_agent.tools)
        return tools

    def find_workflow_by_id(self, workflow_id: str) -> RuntimeWorkflow | None:
        return self.orchestrator.find_workflow_by_id(workflow_id)
