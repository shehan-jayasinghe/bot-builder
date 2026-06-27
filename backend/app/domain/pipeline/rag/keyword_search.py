import logging
from dataclasses import dataclass

from app.infrastructure.keyword.tfidf_index import TfidfIndex

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class KeywordSearchHit:
    text: str
    score: float
    chunk_id: str | None = None


class KeywordSearch:
    def __init__(self, *, tfidf_index: TfidfIndex | None = None) -> None:
        self._tfidf_index = tfidf_index or TfidfIndex()

    def search(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[KeywordSearchHit]:
        raw_hits = self._tfidf_index.search(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
            query=query,
            top_k=top_k,
        )
        return [
            KeywordSearchHit(
                text=str(hit["text"]),
                score=float(hit["score"]),
                chunk_id=hit.get("chunk_id"),
            )
            for hit in raw_hits
        ]
