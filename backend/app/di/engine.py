from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends

from app.di.services import get_assistant_loader, get_tracker_service
from app.domain.engine.dialogue import DialogueEngine
from app.services.assistant_loader import AssistantLoader
from app.services.tracker_service import TrackerService


def get_dialogue_engine_factory(
    assistant_loader: AssistantLoader = Depends(get_assistant_loader),
    tracker_service: TrackerService = Depends(get_tracker_service),
) -> Callable[..., Awaitable[DialogueEngine]]:
    async def factory(
        *,
        webhook_id: str,
        sender_id: str,
        message: str,
        metadata: dict[str, Any],
    ) -> DialogueEngine:
        return await DialogueEngine.from_channel(
            webhook_id=webhook_id,
            sender_id=sender_id,
            message=message,
            metadata=metadata,
            assistant_loader=assistant_loader,
            tracker_service=tracker_service,
        )

    return factory
