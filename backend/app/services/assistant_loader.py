import logging
from typing import Any

from pydantic import ValidationError

from app.domain.models.assistant import DialogueAssistant, LLMConfig
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.channel_repository import ChannelRepository
from app.shared.exceptions.assistant import (
    AgentNotFoundError,
    AssistantLoadError,
    ChannelNotFoundError,
)

logger = logging.getLogger(__name__)


class AssistantLoader:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        agent_repository: AgentRepository,
    ) -> None:
        self._channel_repository = channel_repository
        self._agent_repository = agent_repository

    async def load(self, *, webhook_id: str, metadata: dict[str, Any]) -> DialogueAssistant:
        try:
            channel = await self._find_channel(webhook_id=webhook_id)
            self._resolve_metadata(metadata=metadata, channel=channel)
            agent_doc = await self._find_agent(agent_id=str(channel["agent_id"]))
            assistant = self._to_dialogue_assistant(agent_doc=agent_doc, webhook_id=webhook_id)
            logger.info(
                "Loaded assistant id=%s name=%s for webhook_id=%s",
                assistant.id,
                assistant.name,
                webhook_id,
            )
            return assistant
        except AssistantLoadError:
            raise
        except Exception as e:
            logger.exception("Failed to load assistant for webhook_id=%s", webhook_id)
            raise AssistantLoadError(f"Could not load assistant for webhook_id: {webhook_id}") from e

    async def _find_channel(self, *, webhook_id: str) -> dict[str, Any]:
        channel = await self._channel_repository.find_active_by_webhook_id(webhook_id)
        if channel is None:
            raise ChannelNotFoundError(f"No active channel for webhook_id: {webhook_id}")
        if not channel.get("agent_id"):
            raise AssistantLoadError(f"Channel {webhook_id} is missing agent_id")
        return channel

    async def _find_agent(self, *, agent_id: str) -> dict[str, Any]:
        agent = await self._agent_repository.find_published_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"No published agent for id: {agent_id}")
        return agent

    @staticmethod
    def _resolve_metadata(*, metadata: dict[str, Any], channel: dict[str, Any]) -> None:
        _ = metadata, channel
        # TODO: validate referrer / allowed domains

    @staticmethod
    def _to_dialogue_assistant(*, agent_doc: dict[str, Any], webhook_id: str) -> DialogueAssistant:
        required_fields = ("_id", "name", "system_prompt")
        missing = [field for field in required_fields if not agent_doc.get(field)]
        if missing:
            raise AssistantLoadError(f"Agent document missing required fields: {', '.join(missing)}")

        try:
            llm_config = AssistantLoader._parse_llm_config(agent_doc.get("llm_config"))
            temperature = llm_config.temperature if llm_config else float(agent_doc.get("temperature", 0.7))
            max_output_tokens = (
                llm_config.max_output_tokens if llm_config else int(agent_doc.get("max_output_tokens", 1024))
            )

            return DialogueAssistant(
                id=str(agent_doc["_id"]),
                name=str(agent_doc["name"]),
                webhook_id=webhook_id,
                application_id=AssistantLoader._optional_str(agent_doc.get("application_id")),
                system_prompt=str(agent_doc["system_prompt"]),
                personality=AssistantLoader._optional_str(agent_doc.get("personality")),
                tone=AssistantLoader._optional_str(agent_doc.get("tone")),
                llm_config=llm_config,
                status=str(agent_doc.get("status", "published")),
                skill_ids=AssistantLoader._string_list(agent_doc.get("skill_ids")),
                sub_agent_ids=AssistantLoader._string_list(agent_doc.get("sub_agent_ids")),
                workflow_ids=AssistantLoader._string_list(agent_doc.get("workflow_ids")),
                knowledge_base_ids=AssistantLoader._string_list(agent_doc.get("knowledge_base_ids")),
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except (ValidationError, ValueError, TypeError) as e:
            raise AssistantLoadError("Agent document has invalid field values") from e

    @staticmethod
    def _parse_llm_config(raw: Any) -> LLMConfig | None:
        if not raw or not isinstance(raw, dict):
            return None
        if not raw.get("model_id"):
            return None
        return LLMConfig.model_validate(raw)

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]
