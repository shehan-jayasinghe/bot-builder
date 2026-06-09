from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    sender_id: str = Field(..., examples=["user-123"])
    message: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    recipient_id: str
    text: str


class ChatResponse(BaseModel):
    messages: list[ChatMessage]
