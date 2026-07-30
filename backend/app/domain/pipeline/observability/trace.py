from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.domain.models.tracker import Tracker


class TraceCollector:
    def __init__(self) -> None:
        self._tracker: Tracker | None = None
        self._turn_id: str | None = None
        self._started_at: str | None = None
        self._pending_events: list[dict[str, Any]] = []

    def begin_turn(self) -> str:
        self._turn_id = uuid4().hex
        self._started_at = datetime.now(UTC).isoformat()
        self._pending_events = []
        return self._turn_id

    @property
    def turn_id(self) -> str | None:
        return self._turn_id

    def bind_tracker(self, tracker: Tracker) -> None:
        self._tracker = tracker

    async def record(self, event_type: str, data: dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "at": datetime.now(UTC).isoformat(),
            "data": data,
        }
        self._pending_events.append(event)
        if self._tracker is not None:
            self._tracker.append_trace_event(event)

    def finish_turn(
        self,
        *,
        routing_decision: dict[str, Any] | None,
        turn_evidence: dict[str, Any] | None = None,
    ) -> None:
        if self._tracker is None or self._turn_id is None or self._started_at is None:
            return
        self._tracker.finish_trace_turn(
            turn_id=self._turn_id,
            started_at=self._started_at,
            routing_decision=routing_decision,
            turn_evidence=turn_evidence,
        )
        self._turn_id = None
        self._started_at = None
        self._pending_events = []
