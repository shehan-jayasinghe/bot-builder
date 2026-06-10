from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class ChannelRepository:
    _COLLECTION = "channels"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self._COLLECTION]

    async def find_active_by_webhook_id(self, webhook_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {"webhook_id": webhook_id, "status": "active"},
        )
