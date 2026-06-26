from typing import Any

from app.config import settings
from app.domain.constants.agent_defaults import (
    DEFAULT_PERSONALITY,
    DEFAULT_TONE,
    GuardrailDef,
    merge_guardrails,
)
from app.domain.models.current_user import CurrentUser
from app.infrastructure.ai.prompt_builder import build_system_prompt
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.schemas.agent import (
    AgentListItem,
    AgentType,
    CreateAgentRequest,
    CreateAgentResponse,
    GetAgentResponse,
    GuardrailItem,
    Industry,
    ListAgentsResponse,
    LLMConfigResponse,
)
from app.shared.exceptions.agent import AgentNotFoundError


class AgentService:
    _DEFAULT_TEMPERATURE = 0.7
    _DEFAULT_MAX_OUTPUT_TOKENS = 1024

    def __init__(self, agent_repository: AgentRepository) -> None:
        self._agent_repository = agent_repository

    async def create_draft(
        self,
        *,
        current_user: CurrentUser,
        request: CreateAgentRequest,
    ) -> CreateAgentResponse:
        user_guardrails = self._to_guardrail_defs(request.guardrails)
        guardrails = merge_guardrails(user_guardrails)
        personality = DEFAULT_PERSONALITY
        tone = DEFAULT_TONE
        industry = request.industry.value
        agent_type = request.agent_type.value if request.agent_type else None

        system_prompt = build_system_prompt(
            name=request.name,
            description=request.description,
            industry=industry,
            agent_type=agent_type,
            personality=personality,
            tone=tone,
            guardrails=guardrails,
        )

        llm_config = LLMConfigResponse(
            model_id=settings.bedrock_model_id,
            region=settings.aws_region,
            temperature=self._DEFAULT_TEMPERATURE,
            max_output_tokens=self._DEFAULT_MAX_OUTPUT_TOKENS,
        )

        document = {
            "name": request.name,
            "description": request.description,
            "industry": industry,
            "agent_type": agent_type,
            "system_prompt": system_prompt,
            "personality": personality,
            "tone": tone,
            "guardrails": guardrails,
            "llm_config": llm_config.model_dump(),
            "status": "draft",
            "organization_id": current_user.organization_id,
            "created_by": current_user.user_id,
            "skill_ids": [],
            "workflow_ids": [],
            "sub_agent_ids": [],
            "tool_ids": [],
            "knowledge_base_ids": [],
        }

        saved = await self._agent_repository.create(document=document)
        return self._document_to_response(saved)

    async def get_by_id(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
    ) -> GetAgentResponse:
        document = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if document is None:
            raise AgentNotFoundError("Agent not found")
        return self._document_to_response(document)

    async def list_by_organization(
        self,
        *,
        current_user: CurrentUser,
        status: str | None = None,
    ) -> ListAgentsResponse:
        documents = await self._agent_repository.find_all_by_organization(
            organization_id=current_user.organization_id,
            status=status,
        )
        items = [self._document_to_list_item(document) for document in documents]
        return ListAgentsResponse(items=items, total=len(items))

    @staticmethod
    def _document_to_list_item(document: dict[str, Any]) -> AgentListItem:
        agent_type = document.get("agent_type")
        return AgentListItem(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            industry=Industry(document["industry"]),
            agent_type=AgentType(agent_type) if agent_type else None,
            status=str(document.get("status", "draft")),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
        )

    @staticmethod
    def _document_to_response(document: dict[str, Any]) -> GetAgentResponse:
        guardrails = document.get("guardrails") or []
        llm_config_raw = document.get("llm_config") or {}
        agent_type = document.get("agent_type")

        return GetAgentResponse(
            id=str(document["_id"]),
            name=str(document["name"]),
            description=document.get("description"),
            industry=Industry(document["industry"]),
            agent_type=AgentType(agent_type) if agent_type else None,
            system_prompt=str(document["system_prompt"]),
            personality=str(document.get("personality", "")),
            tone=str(document.get("tone", "")),
            guardrails=[GuardrailItem(**item) for item in guardrails],
            llm_config=LLMConfigResponse(**llm_config_raw),
            status=str(document.get("status", "draft")),
            organization_id=str(document["organization_id"]),
            created_at=document["created_at"],
        )

    @staticmethod
    def _to_guardrail_defs(guardrails: list[GuardrailItem] | None) -> list[GuardrailDef] | None:
        if not guardrails:
            return None
        return [GuardrailDef(**item.model_dump()) for item in guardrails]
