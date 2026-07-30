from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.domain.models.source_document import ChunkDocument


class KbChunkRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[settings.kb_chunks_collection]

    async def insert_many(
        self,
        *,
        knowledgebase_id: str,
        organization_id: str,
        chunks: list[ChunkDocument],
    ) -> None:
        if not chunks:
            return

        now = datetime.now(UTC)
        documents: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks):
            documents.append(
                {
                    "knowledgebase_id": knowledgebase_id,
                    "organization_id": organization_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "metadata": chunk.metadata,
                    "index": index,
                    "created_at": now,
                }
            )

        await self._collection.insert_many(documents)

    async def list_by_knowledgebase(self, *, knowledgebase_id: str) -> list[dict[str, Any]]:
        cursor = self._collection.find({"knowledgebase_id": knowledgebase_id}).sort("index", 1)
        return await cursor.to_list(length=None)

    async def delete_by_knowledgebase(self, *, knowledgebase_id: str) -> None:
        await self._collection.delete_many({"knowledgebase_id": knowledgebase_id})
