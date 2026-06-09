from typing import Any


class Tracker:
    """Session and conversation history for one sender + assistant pair."""

    def __init__(self, sender_id: str, assistant_id: str) -> None:
        self._sender_id = sender_id
        self._assistant_id = assistant_id
        self._events: list[dict[str, Any]] = []

    @classmethod
    async def load_or_create(
        cls,
        *,
        sender_id: str,
        assistant_id: str,
        message: str,
        metadata: dict[str, Any],
    ) -> "Tracker":
        """
        Load an existing tracker or start a new session.

        TODO:
          - load from MongoDB by sender_id + assistant_id
          - check Redis session timeout
          - restore active flow state
        """
        tracker = cls(sender_id=sender_id, assistant_id=assistant_id)
        tracker._events.append(
            {
                "role": "user",
                "content": message,
                "metadata": metadata,
            },
        )
        return tracker

    def get_history(self) -> list[dict[str, Any]]:
        return self._events

    async def persist(self, assistant_replies: list[str]) -> None:
        """
        Save conversation events after a turn completes.

        TODO:
          - append assistant events to in-memory tracker
          - persist full event log to MongoDB
          - update Redis session TTL
        """
        for reply in assistant_replies:
            self._events.append({"role": "assistant", "content": reply})
