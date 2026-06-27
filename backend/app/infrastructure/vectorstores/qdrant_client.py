import logging
import uuid
from typing import Any

from qdrant_client.http.models import PointStruct

from app.config import settings
from app.domain.models.source_document import ChunkDocument
from app.infrastructure.ai.bedrock_embeddings import BedrockEmbeddings
from app.infrastructure.connectors.qdrant.qdrant_connector import QdrantConnector

logger = logging.getLogger(__name__)


class QdrantVectorIndex:
    def __init__(
        self,
        *,
        qdrant: QdrantConnector | None = None,
        embeddings: BedrockEmbeddings | None = None,
    ) -> None:
        self._qdrant = qdrant or QdrantConnector(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._embeddings = embeddings or BedrockEmbeddings()

    def upsert_chunks(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str:
        collection_name = self._collection_name(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        self._ensure_collection(collection_name=collection_name)

        texts = [chunk.text for chunk in chunks]
        vectors = self._embeddings.embed_documents(texts)

        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=vector,
                payload={
                    "knowledgebase_id": knowledgebase_id,
                    "organization_id": organization_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self._qdrant.upsert_points(collection_name=collection_name, points=points)
        logger.info("Upserted %s vectors to Qdrant collection %s", len(points), collection_name)
        return collection_name

    def _ensure_collection(self, *, collection_name: str) -> None:
        client = self._qdrant._get_client()
        existing = {collection.name for collection in client.get_collections().collections}
        if collection_name in existing:
            return
        self._qdrant.create_collection(
            collection_name=collection_name,
            vector_size=self._embeddings.dimensions,
        )

    @staticmethod
    def _collection_name(*, organization_id: str, knowledgebase_id: str) -> str:
        return f"kb_{organization_id}_{knowledgebase_id}"

    def search(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.7,
    ) -> list[dict[str, Any]]:
        collection_name = self._collection_name(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        query_vector = self._embeddings.embed_query(query)
        raw_hits = self._qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
        )

        hits: list[dict[str, Any]] = []
        for hit in raw_hits:
            score = float(getattr(hit, "score", 0.0))
            if score < min_score:
                continue
            payload = getattr(hit, "payload", None) or {}
            text = str(payload.get("text", "")).strip()
            if not text:
                continue
            hits.append(
                {
                    "text": text,
                    "score": score,
                    "chunk_id": payload.get("chunk_id"),
                },
            )
        return hits
