from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorDatabase

from app.config import settings


class OrganizationRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.organizations_collection]

    async def create(
        self,
        *,
        name: str,
        industry: str | None,
        owner_user_id: str | None = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        document = {
            "name": name,
            "industry": industry,
            "owner_user_id": owner_user_id,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def find_by_id(self, organization_id: str) -> dict[str, Any] | None:
        object_id = self._to_object_id(organization_id)
        if object_id is None:
            return None
        return await self._collection.find_one({"_id": object_id})

    async def delete_by_id(self, organization_id: Any) -> None:
        await self._collection.delete_one({"_id": organization_id})

    async def set_owner(
        self,
        *,
        organization_id: Any,
        owner_user_id: str,
        session: AsyncIOMotorClientSession | None = None,
    ) -> None:
        await self._collection.update_one(
            {"_id": organization_id},
            {"$set": {"owner_user_id": owner_user_id, "updated_at": datetime.now(UTC)}},
            session=session,
        )

    @staticmethod
    def _to_object_id(organization_id: str) -> ObjectId | None:
        try:
            return ObjectId(organization_id)
        except (InvalidId, TypeError):
            return None
