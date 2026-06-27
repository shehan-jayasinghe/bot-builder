from typing import Any

from pydantic import BaseModel, Field

from app.domain.models.assistant import LLMConfig


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
