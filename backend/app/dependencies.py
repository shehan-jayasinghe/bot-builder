from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends

from app.core.engine.dialogue import DialogueEngine
from app.core.services.assistant_loader import AssistantLoader


def get_assistant_loader() -> AssistantLoader:
    return AssistantLoader()


def get_dialogue_engine_factory(
    assistant_loader: AssistantLoader = Depends(get_assistant_loader),
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
        )

    return factory
