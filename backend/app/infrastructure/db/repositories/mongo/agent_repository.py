from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class AgentRepository:
    _COLLECTION = "agents"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self._COLLECTION]

    async def create(self, *, document: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_published_by_id(self, agent_id: str) -> dict[str, Any] | None:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return None

        return await self._collection.find_one(
            {"_id": object_id, "status": "published"},
        )

    async def find_by_id_for_organization(
        self,
        *,
        agent_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return None

        return await self._collection.find_one(
            {"_id": object_id, "organization_id": organization_id},
        )

    async def find_all_by_organization(
        self,
        *,
        organization_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"organization_id": organization_id}
        if status is not None:
            query["status"] = status

        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    def _to_object_id(agent_id: str) -> ObjectId | None:
        try:
            return ObjectId(agent_id)
        except (InvalidId, TypeError):
            return None
