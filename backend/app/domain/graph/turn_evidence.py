from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.pipeline.rag.rag_result import RagChunk


@dataclass
class TurnEvidence:
    user_message: str
    assistant_replies: list[str] = field(default_factory=list)
    rag_retrievals: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=dict)

    def record_rag_retrieval(self, *, query: str, chunks: list[RagChunk]) -> None:
        self.rag_retrievals.append(
            {
                "query": query,
                "chunks": [_rag_chunk_to_dict(chunk) for chunk in chunks],
            },
        )

    def record_tool_call(
        self,
        *,
        name: str,
        arguments: dict[str, Any],
        status: str,
    ) -> None:
        self.tool_calls.append(
            {
                "name": name,
                "arguments": arguments,
                "status": status,
            },
        )

    def set_assistant_replies(self, replies: list[str]) -> None:
        self.assistant_replies = list(replies)

    def set_routing(self, routing: dict[str, Any]) -> None:
        self.routing = dict(routing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_message": self.user_message,
            "assistant_replies": list(self.assistant_replies),
            "rag_retrievals": list(self.rag_retrievals),
            "tool_calls": list(self.tool_calls),
            "routing": dict(self.routing),
        }


def _rag_chunk_to_dict(chunk: RagChunk) -> dict[str, Any]:
    return {
        "rank": chunk.rank,
        "text": chunk.text,
        "score": chunk.score,
        "chunk_id": chunk.chunk_id,
        "kb_id": chunk.kb_id,
        "kb_name": chunk.kb_name,
    }
