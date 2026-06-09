from typing import Any

from app.core.engine.flow_manager import FlowManager
from app.core.engine.tracker import Tracker
from app.core.models.assistant import DialogueAssistant
from app.core.services.assistant_loader import AssistantLoader
from app.schemas.chat import ChatMessage


class DialogueEngine:
    """
    Central orchestrator for a single chat turn.

    Same role as Convoz DialogueEngine, without Sanic coupling.
    """

    def __init__(
        self,
        sender_id: str,
        message: str,
        assistant: DialogueAssistant,
        tracker: Tracker,
        flow_manager: FlowManager,
    ) -> None:
        self._sender_id = sender_id
        self._message = message
        self._assistant = assistant
        self._tracker = tracker
        self._flow_manager = flow_manager

    @classmethod
    async def from_channel(
        cls,
        *,
        webhook_id: str,
        sender_id: str,
        message: str,
        metadata: dict[str, Any],
        assistant_loader: AssistantLoader,
    ) -> "DialogueEngine":
        # Step 1: Load assistant config
        assistant = await assistant_loader.load(webhook_id=webhook_id, metadata=metadata)

        # Step 2: Load or create session tracker
        tracker = await Tracker.load_or_create(
            sender_id=sender_id,
            assistant_id=assistant.id,
            message=message,
            metadata=metadata,
        )

        # Step 3: Wire flow manager
        flow_manager = FlowManager(
            assistant=assistant,
            tracker=tracker,
            user_message=message,
        )

        return cls(
            sender_id=sender_id,
            message=message,
            assistant=assistant,
            tracker=tracker,
            flow_manager=flow_manager,
        )

    async def run(self) -> list[ChatMessage]:
        # Step 4: Run flow (Bedrock inside FlowManager)
        raw_replies = await self._flow_manager.handle_message()

        # Step 5: Persist tracker events
        await self._tracker.persist(raw_replies)

        # Step 6: Format for API response
        return [
            ChatMessage(recipient_id=self._sender_id, text=reply)
            for reply in raw_replies
        ]
