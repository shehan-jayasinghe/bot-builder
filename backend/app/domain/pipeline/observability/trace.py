from typing import Any


class TraceCollector:
    async def record(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Record a trace event for the current conversation turn.

        TODO:
          - persist events to MongoDB
          - expose via GET /api/v1/conversations/{id}/trace
          - include timestamps for trace view UI
        """
        _ = event_type, data
        pass
