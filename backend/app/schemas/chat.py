from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    sender_id: str = Field(..., examples=["user-123"])
    message: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatButton(BaseModel):
    title: str
    payload: str


class ChatMessage(BaseModel):
    recipient_id: str
    text: str | None = None
    buttons: list[ChatButton] | None = None

    # TODO: quick_replies, custom cards, images (match preview UI)


class ChatResponse(BaseModel):
    messages: list[ChatMessage]
