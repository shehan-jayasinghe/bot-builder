from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Industry(StrEnum):
    FINANCIAL_SERVICES = "financial_services"
    LOGISTICS = "logistics"
    TRAVEL = "travel"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    OTHER = "other"


class AgentType(StrEnum):
    PAYMENT_COLLECTIONS = "payment_collections"
    CUSTOMER_ONBOARDING = "customer_onboarding"
    CUSTOMER_SUPPORT_TRIAGE = "customer_support_triage"


class AgentStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class GuardrailItem(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    instruction: str = Field(min_length=1, max_length=1000)
    enabled: bool = True


class CreateAgentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    industry: Industry
    agent_type: AgentType | None = None
    guardrails: list[GuardrailItem] | None = None


class LLMConfigResponse(BaseModel):
    model_id: str
    region: str
    temperature: float
    max_output_tokens: int


class CreateAgentResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    industry: Industry
    agent_type: AgentType | None = None
    system_prompt: str
    personality: str
    tone: str
    guardrails: list[GuardrailItem]
    llm_config: LLMConfigResponse
    status: str = "draft"
    organization_id: str
    created_at: datetime


GetAgentResponse = CreateAgentResponse


class AgentListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    industry: Industry
    agent_type: AgentType | None = None
    status: str
    organization_id: str
    created_at: datetime


class ListAgentsResponse(BaseModel):
    items: list[AgentListItem]
    total: int
