from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class ConnectorRepository:
    _COLLECTION = "connectors"

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
        connector_id: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(connector_id)
        if object_id is None:
            return None
        return await self._collection.find_one(
            {"_id": object_id, "organization_id": organization_id},
        )

    async def find_by_name_for_organization(
        self,
        *,
        name: str,
        organization_id: str,
    ) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {"name": name, "organization_id": organization_id},
        )

    async def find_by_ids_for_organization(
        self,
        *,
        organization_id: str,
        connector_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not connector_ids:
            return []
        object_ids = [
            oid for connector_id in connector_ids if (oid := self._to_object_id(connector_id))
        ]
        if not object_ids:
            return []
        cursor = self._collection.find(
            {"_id": {"$in": object_ids}, "organization_id": organization_id},
        )
        return await cursor.to_list(length=None)

    async def find_all_by_organization(
        self,
        *,
        organization_id: str,
        connector_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"organization_id": organization_id}
        if connector_type is not None:
            query["type"] = connector_type
        if status is not None:
            query["status"] = status
        cursor = self._collection.find(query).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def update(
        self,
        *,
        connector_id: str,
        organization_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        object_id = self._to_object_id(connector_id)
        if object_id is None:
            return None
        updates["updated_at"] = datetime.now(UTC)
        return await self._collection.find_one_and_update(
            {"_id": object_id, "organization_id": organization_id},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )

    async def delete(
        self,
        *,
        connector_id: str,
        organization_id: str,
    ) -> bool:
        object_id = self._to_object_id(connector_id)
        if object_id is None:
            return False
        result = await self._collection.delete_one(
            {"_id": object_id, "organization_id": organization_id},
        )
        return result.deleted_count > 0

    @staticmethod
    def _to_object_id(connector_id: str) -> ObjectId | None:
        try:
            return ObjectId(connector_id)
        except (InvalidId, TypeError):
            return None
