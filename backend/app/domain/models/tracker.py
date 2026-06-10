from datetime import UTC, datetime
from typing import Any


class Tracker:
    """In-memory session and conversation history for one sender + assistant pair."""

    def __init__(
        self,
        sender_id: str,
        assistant_id: str,
        *,
        events: list[dict[str, Any]] | None = None,
        active_flow_state: dict[str, Any] | None = None,
    ) -> None:
        self._sender_id = sender_id
        self._assistant_id = assistant_id
        self._events: list[dict[str, Any]] = list(events or [])
        self._active_flow_state = active_flow_state

    @property
    def sender_id(self) -> str:
        return self._sender_id

    @property
    def assistant_id(self) -> str:
        return self._assistant_id

    @property
    def active_flow_state(self) -> dict[str, Any] | None:
        return self._active_flow_state

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "Tracker":
        return cls(
            sender_id=data["sender_id"],
            assistant_id=data["assistant_id"],
            events=data.get("events", []),
            active_flow_state=data.get("active_flow_state"),
        )

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> "Tracker":
        return cls(
            sender_id=doc["sender_id"],
            assistant_id=doc["assistant_id"],
            events=doc.get("events", []),
            active_flow_state=doc.get("active_flow_state"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "sender_id": self._sender_id,
            "assistant_id": self._assistant_id,
            "events": self._events,
            "active_flow_state": self._active_flow_state,
        }

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._events)

    def set_active_flow_state(self, state: dict[str, Any] | None) -> None:
        self._active_flow_state = state

    def append_user_message(self, *, message: str, metadata: dict[str, Any]) -> None:
        self._events.append(
            {
                "role": "user",
                "content": message,
                "metadata": metadata,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    def append_assistant_replies(self, replies: list[str]) -> None:
        now = datetime.now(UTC).isoformat()
        for reply in replies:
            self._events.append(
                {
                    "role": "assistant",
                    "content": reply,
                    "timestamp": now,
                },
            )
