from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class WorkflowRepository:
    _COLLECTION = "workflows"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self._COLLECTION]

    async def create(self, *, document: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def count_by_organization(self, *, organization_id: str) -> int:
        return await self._collection.count_documents({"organization_id": organization_id})

    async def find_by_ids_for_organization(
        self,
        *,
        organization_id: str,
        workflow_ids: list[str],
        status: str | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if not workflow_ids:
            return []
        object_ids = [
            oid for workflow_id in workflow_ids if (oid := self._to_object_id(workflow_id))
        ]
        if not object_ids:
            return []
        query: dict[str, Any] = {
            "_id": {"$in": object_ids},
            "organization_id": organization_id,
        }
        if status is not None:
            query["status"] = status
        if agent_id is not None:
            query["agent_id"] = agent_id
        cursor = self._collection.find(query)
        return await cursor.to_list(length=None)

    async def find_all_by_organization(
        self,
        *,
        organization_id: str,
        status: str | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"organization_id": organization_id}
        if status is not None:
            query["status"] = status
        if agent_id is not None:
            query["agent_id"] = agent_id
        cursor = self._collection.find(query).sort("updated_at", -1)
        return await cursor.to_list(length=None)

    async def find_by_id_for_organization(
        self,
        *,
        workflow_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(workflow_id)
        if object_id is None:
            return None
        return await self._collection.find_one(
            {"_id": object_id, "organization_id": organization_id},
        )

    async def update(
        self,
        *,
        workflow_id: str,
        organization_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(workflow_id)
        if object_id is None:
            return None
        updates["updated_at"] = datetime.now(UTC)
        return await self._collection.find_one_and_update(
            {"_id": object_id, "organization_id": organization_id},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    def _to_object_id(workflow_id: str) -> ObjectId | None:
        try:
            return ObjectId(workflow_id)
        except (InvalidId, TypeError):
            return None
