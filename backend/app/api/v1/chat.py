from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends

from app.domain.engine.dialogue import DialogueEngine
from app.domain.pipeline.chat_pipeline import ChatPipeline
from app.di import get_chat_pipeline, get_dialogue_engine_factory
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/webhook/{webhook_id}", response_model=ChatResponse)
async def chat_webhook(
    webhook_id: str,
    body: ChatRequest,
    engine_factory: Callable[..., Awaitable[DialogueEngine]] = Depends(get_dialogue_engine_factory),
    chat_pipeline: ChatPipeline = Depends(get_chat_pipeline),
) -> ChatResponse:
    """
    Main chat endpoint — entry point for the inference flow.

    Flow:
      1. Validate request (Pydantic)
      2. Build DialogueEngine
      3. ChatPipeline (guardrails → RAG → skills → engine)
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
    messages = await chat_pipeline.run(engine)
    return ChatResponse(messages=messages)
