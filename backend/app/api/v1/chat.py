from fastapi import APIRouter, Depends

from app.di.chat import get_chat_completion_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_completion_service import ChatCompletionService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/webhook/{webhook_id}", response_model=ChatResponse)
async def chat_webhook(
    webhook_id: str,
    body: ChatRequest,
    chat_service: ChatCompletionService = Depends(get_chat_completion_service),
) -> ChatResponse:
    """
    Main chat endpoint — entry point for the inference flow.

    Flow:
      1. Validate request (Pydantic)
      2. Resolve channel + published agent (friendly 200 fallback)
      3. Load tracker + RuntimeBundle
      4. Sanitize + guardrails + orchestrator LLM (+ tools when attached)
      5. Persist session and return JSON replies
    """
    return await chat_service.complete(webhook_id=webhook_id, request=body)
