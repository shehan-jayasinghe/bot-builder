from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ToolRepository:
    _COLLECTION = "tools"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self._COLLECTION]

    async def create(self, *, document: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_by_id_for_organization(
        self,
        *,
        tool_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(tool_id)
        if object_id is None:
            return None
        return await self._collection.find_one(
            {
                "_id": object_id,
                "organization_id": organization_id,
            },
        )

    async def find_by_id_for_agent(
        self,
        *,
        tool_id: str,
        agent_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(tool_id)
        if object_id is None:
            return None
        return await self._collection.find_one(
            {
                "_id": object_id,
                "agent_id": agent_id,
                "organization_id": organization_id,
            },
        )

    async def find_by_name_for_agent(
        self,
        *,
        name: str,
        agent_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {
                "name": name,
                "agent_id": agent_id,
                "organization_id": organization_id,
            },
        )

    async def find_all_by_agent(
        self,
        *,
        agent_id: str,
        organization_id: str,
        executor: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "agent_id": agent_id,
            "organization_id": organization_id,
        }
        if executor is not None:
            query["executor"] = executor
        if status is not None:
            query["status"] = status
        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def find_by_ids_for_organization(
        self,
        *,
        organization_id: str,
        tool_ids: list[str],
        agent_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if not tool_ids:
            return []
        object_ids = [oid for tool_id in tool_ids if (oid := self._to_object_id(tool_id))]
        if not object_ids:
            return []
        query: dict[str, Any] = {
            "_id": {"$in": object_ids},
            "organization_id": organization_id,
        }
        if agent_id is not None:
            query["agent_id"] = agent_id
        if status is not None:
            query["status"] = status
        cursor = self._collection.find(query)
        return await cursor.to_list(length=None)

    async def find_all_by_organization(
        self,
        *,
        organization_id: str,
        agent_id: str | None = None,
        executor: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"organization_id": organization_id}
        if agent_id is not None:
            query["agent_id"] = agent_id
        if executor is not None:
            query["executor"] = executor
        if status is not None:
            query["status"] = status
        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def update(
        self,
        *,
        tool_id: str,
        organization_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(tool_id)
        if object_id is None:
            return None

        updates = {**updates, "updated_at": datetime.now(UTC)}
        result = await self._collection.find_one_and_update(
            {"_id": object_id, "organization_id": organization_id},
            {"$set": updates},
            return_document=True,
        )
        return result

    @staticmethod
    def _to_object_id(value: str) -> ObjectId | None:
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None
