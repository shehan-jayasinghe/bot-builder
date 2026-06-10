from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class AgentRepository:
    _COLLECTION = "agents"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self._COLLECTION]

    async def find_published_by_id(self, agent_id: str) -> dict[str, Any] | None:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return None

        return await self._collection.find_one(
            {"_id": object_id, "status": "published"},
        )

    @staticmethod
    def _to_object_id(agent_id: str) -> ObjectId | None:
        try:
            return ObjectId(agent_id)
        except (InvalidId, TypeError):
            return None
