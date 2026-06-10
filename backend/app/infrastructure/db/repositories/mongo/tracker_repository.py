from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.domain.models.tracker import Tracker


class TrackerRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.tracker_collection]

    async def find_by_session(self, *, sender_id: str, assistant_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {"sender_id": sender_id, "assistant_id": assistant_id},
        )

    async def upsert(self, tracker: Tracker) -> None:
        now = datetime.now(UTC)
        await self._collection.update_one(
            {"sender_id": tracker.sender_id, "assistant_id": tracker.assistant_id},
            {
                "$set": {
                    "sender_id": tracker.sender_id,
                    "assistant_id": tracker.assistant_id,
                    "events": tracker.get_history(),
                    "active_flow_state": tracker.active_flow_state,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
