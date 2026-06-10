from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    model_id: str
    region: str = "us-east-1"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=1024, ge=1)


class DialogueAssistant(BaseModel):
    id: str
    name: str
    webhook_id: str
    system_prompt: str
    application_id: str | None = None
    personality: str | None = None
    tone: str | None = None
    llm_config: LLMConfig | None = None
    status: str = "published"
    skill_ids: list[str] = Field(default_factory=list)
    sub_agent_ids: list[str] = Field(default_factory=list)
    workflow_ids: list[str] = Field(default_factory=list)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    temperature: float = Field(default=0.7)
    max_output_tokens: int = Field(default=1024)

    def build_system_prompt(self) -> str:
        parts = [self.system_prompt]
        if self.personality:
            parts.append(f"Personality: {self.personality}")
        if self.tone:
            parts.append(f"Tone: {self.tone}")
        return "\n\n".join(parts)
