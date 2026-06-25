import logging
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)


class QdrantConnector:
    """Vector DB connector for semantic knowledge bases."""

    def __init__(self, *, url: str | None = None, api_key: str | None = None) -> None:
        self._url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self._api_key = api_key or os.getenv("QDRANT_API_KEY")
        self._client: Any = None

    @property
    def url(self) -> str:
        return self._url

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            kwargs: dict[str, Any] = {"url": self._url}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = QdrantClient(**kwargs)
        return self._client

    def ping(self) -> bool:
        try:
            self._get_client().get_collections()
            return True
        except Exception:
            logger.warning("Qdrant not reachable at %s", self._url)
            return False

    def create_collection(
        self,
        *,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
    ) -> None:
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT,
        }
        self._get_client().create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance_map.get(distance, Distance.COSINE),
            ),
        )

    def upsert_points(
        self,
        *,
        collection_name: str,
        points: list[Any],
    ) -> None:
        self._get_client().upsert(collection_name=collection_name, points=points)

    def search(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[Any]:
        return self._get_client().search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
        )

    def delete_collection(self, *, collection_name: str) -> None:
        self._get_client().delete_collection(collection_name=collection_name)
