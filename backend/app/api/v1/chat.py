from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Depends

from app.core.engine.dialogue import DialogueEngine
from app.dependencies import get_dialogue_engine_factory
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/webhook/{webhook_id}", response_model=ChatResponse)
async def chat_webhook(
    webhook_id: str,
    body: ChatRequest,
    engine_factory: Callable[..., Awaitable[DialogueEngine]] = Depends(get_dialogue_engine_factory),
) -> ChatResponse:
    """
    Main chat endpoint — entry point for the inference flow.

    Flow:
      1. Validate request (Pydantic)
      2. Build DialogueEngine
      3. Run engine
      4. Return JSON replies
    """
    # TODO: add auth (API token / service token)
    # TODO: add rate limiting per webhook_id

    engine = await engine_factory(
        webhook_id=webhook_id,
        sender_id=body.sender_id,
        message=body.message,
        metadata=body.metadata,
    )
    messages = await engine.run()
    return ChatResponse(messages=messages)
