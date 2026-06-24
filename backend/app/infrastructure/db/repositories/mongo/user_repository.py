from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorDatabase

from app.config import settings


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.users_collection]

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"email": email.lower()})

    async def find_by_clerk_id(self, clerk_id: str) -> dict[str, Any] | None:
        return await self._collection.find_one({"clerk_id": clerk_id})

    async def create(
        self,
        *,
        clerk_id: str,
        email: str,
        first_name: str,
        last_name: str,
        organization_id: Any,
        user_type: str = "owner",
        is_root: bool = True,
        session: AsyncIOMotorClientSession | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        document = {
            "clerk_id": clerk_id,
            "email": email.lower(),
            "first_name": first_name,
            "last_name": last_name,
            "organization_id": organization_id,
            "user_type": user_type,
            "is_root": is_root,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return document

    async def delete_by_id(self, user_id: Any) -> None:
        await self._collection.delete_one({"_id": user_id})
