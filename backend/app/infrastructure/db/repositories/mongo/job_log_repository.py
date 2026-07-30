from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings


class JobLogRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.job_logs_collection]

    async def create(self, *, document: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)

        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def update_status(self, *, job_id: str, status: str) -> None:
        object_id = self._to_object_id(job_id)
        if object_id is None:
            raise ValueError(f"Invalid job_id: {job_id}")

        await self._collection.update_one(
            {"_id": object_id},
            {"$set": {"status": status, "updated_at": datetime.now(UTC)}},
        )

    @staticmethod
    def _to_object_id(value: str) -> ObjectId | None:
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None
