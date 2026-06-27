import logging
from dataclasses import dataclass
from typing import Any

from app.infrastructure.vectorstores.qdrant_client import QdrantVectorIndex

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.7


@dataclass(frozen=True)
class VectorSearchHit:
    text: str
    score: float
    chunk_id: str | None = None


class VectorSearch:
    def __init__(self, *, vector_index: QdrantVectorIndex | None = None) -> None:
        self._vector_index = vector_index or QdrantVectorIndex()

    def search(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> list[VectorSearchHit]:
        raw_hits = self._vector_index.search(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
            query=query,
            top_k=top_k,
            min_score=min_score,
        )
        return [
            VectorSearchHit(
                text=str(hit["text"]),
                score=float(hit["score"]),
                chunk_id=hit.get("chunk_id"),
            )
            for hit in raw_hits
        ]
