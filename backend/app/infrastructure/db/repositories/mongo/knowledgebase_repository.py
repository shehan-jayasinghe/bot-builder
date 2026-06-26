from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings


class KnowledgebaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.knowledgebases_collection]

    async def create(
        self,
        *,
        document: dict[str, Any],
        knowledgebase_id: ObjectId | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        if knowledgebase_id is not None:
            document["_id"] = knowledgebase_id

        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_by_id(self, knowledgebase_id: str) -> dict[str, Any] | None:
        object_id = self._to_object_id(knowledgebase_id)
        if object_id is None:
            return None
        return await self._collection.find_one({"_id": object_id})

    async def find_by_id_for_organization(
        self,
        *,
        knowledgebase_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(knowledgebase_id)
        if object_id is None:
            return None
        return await self._collection.find_one(
            {
                "_id": object_id,
                "organization_id": organization_id,
            },
        )

    async def find_all_by_organization(
        self,
        *,
        organization_id: str,
        agent_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"organization_id": organization_id}
        if agent_id is not None:
            query["agent_id"] = agent_id
        if status is not None:
            query["status"] = status

        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def update(
        self,
        *,
        knowledgebase_id: str,
        organization_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(knowledgebase_id)
        if object_id is None:
            return None

        updates = {**updates, "updated_at": datetime.now(UTC)}
        result = await self._collection.find_one_and_update(
            {"_id": object_id, "organization_id": organization_id},
            {"$set": updates},
            return_document=True,
        )
        return result

    async def update_status(self, *, knowledgebase_id: str, status: str) -> None:
        object_id = self._to_object_id(knowledgebase_id)
        if object_id is None:
            raise ValueError(f"Invalid knowledgebase_id: {knowledgebase_id}")

        await self._collection.update_one(
            {"_id": object_id},
            {"$set": {"status": status, "updated_at": datetime.now(UTC)}},
        )

    async def find_all_by_agent(
        self,
        *,
        organization_id: str,
        agent_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "organization_id": organization_id,
            "agent_id": agent_id,
        }
        if status is not None:
            query["status"] = status

        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    def _to_object_id(value: str) -> ObjectId | None:
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None
