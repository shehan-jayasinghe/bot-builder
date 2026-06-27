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

    async def push_tool_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        tool_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$addToSet": {"tool_ids": tool_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def pull_tool_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        tool_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$pull": {"tool_ids": tool_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def push_knowledge_base_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        knowledgebase_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$addToSet": {"knowledge_base_ids": knowledgebase_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def pull_knowledge_base_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        knowledgebase_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$pull": {"knowledge_base_ids": knowledgebase_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def push_workflow_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        workflow_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$addToSet": {"workflow_ids": workflow_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def pull_workflow_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        workflow_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$pull": {"workflow_ids": workflow_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def push_sub_agent_id(
        self,
        *,
        agent_id: str,
        organization_id: str,
        sub_agent_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$addToSet": {"sub_agent_ids": sub_agent_id},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    async def upsert_capability_catalog_entry(
        self,
        *,
        agent_id: str,
        organization_id: str,
        section: str,
        resource_id: str,
        routing_hint: str | None = None,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        entry: dict[str, Any] = {}
        if routing_hint is not None:
            entry["routing_hint"] = routing_hint
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$set": {
                    f"capability_catalog.{section}.{resource_id}": entry,
                    "updated_at": datetime.now(UTC),
                },
            },
        )
        return result.matched_count > 0

    async def remove_capability_catalog_entry(
        self,
        *,
        agent_id: str,
        organization_id: str,
        section: str,
        resource_id: str,
    ) -> bool:
        object_id = self._to_object_id(agent_id)
        if object_id is None:
            return False
        result = await self._collection.update_one(
            {"_id": object_id, "organization_id": organization_id},
            {
                "$unset": {f"capability_catalog.{section}.{resource_id}": ""},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.matched_count > 0

    @staticmethod
    def _to_object_id(agent_id: str) -> ObjectId | None:
        try:
            return ObjectId(agent_id)
        except (InvalidId, TypeError):
            return None
