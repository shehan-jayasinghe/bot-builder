from typing import Any

from app.domain.engine.flow_manager import FlowManager
from app.domain.models.tracker import Tracker
from app.domain.models.assistant import DialogueAssistant
from app.services.assistant_loader import AssistantLoader
from app.services.tracker_service import TrackerService
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
        tracker_service: TrackerService,
        flow_manager: FlowManager,
    ) -> None:
        self._sender_id = sender_id
        self._message = message
        self._assistant = assistant
        self._tracker = tracker
        self._tracker_service = tracker_service
        self._flow_manager = flow_manager

    @property
    def sender_id(self) -> str:
        return self._sender_id

    @property
    def message(self) -> str:
        return self._message

    @property
    def assistant(self) -> DialogueAssistant:
        return self._assistant

    @property
    def tracker(self) -> Tracker:
        return self._tracker

    @classmethod
    async def from_channel(
        cls,
        *,
        webhook_id: str,
        sender_id: str,
        message: str,
        metadata: dict[str, Any],
        assistant_loader: AssistantLoader,
        tracker_service: TrackerService,
    ) -> "DialogueEngine":
        # Step 1: Load assistant config
        assistant = await assistant_loader.load(webhook_id=webhook_id, metadata=metadata)

        # Step 2: Load or create session tracker
        tracker = await tracker_service.load_or_create(
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
            tracker_service=tracker_service,
            flow_manager=flow_manager,
        )

    async def run(self) -> list[ChatMessage]:
        # Step 4: Run flow (Bedrock inside FlowManager)
        raw_replies = await self._flow_manager.handle_message()

        # Step 5: Persist tracker events
        await self._tracker_service.persist(self._tracker, raw_replies)

        # Step 6: Format for API response
        return [
            ChatMessage(recipient_id=self._sender_id, text=reply)
            for reply in raw_replies
        ]
