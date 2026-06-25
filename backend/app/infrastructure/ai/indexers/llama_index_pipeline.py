import logging

from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.domain.models.source_document import ChunkDocument
from app.infrastructure.graph.neo4j_client import Neo4jGraphIndex
from app.infrastructure.keyword.tfidf_index import TfidfIndex
from app.infrastructure.vectorstores.qdrant_client import QdrantVectorIndex

logger = logging.getLogger(__name__)


class LlamaIndexPipeline:
    """Route indexing by storage_type (vector, keyword, graph)."""

    def __init__(
        self,
        *,
        vector_index: QdrantVectorIndex | None = None,
        keyword_index: TfidfIndex | None = None,
        graph_index: Neo4jGraphIndex | None = None,
    ) -> None:
        self._vector_index = vector_index or QdrantVectorIndex()
        self._keyword_index = keyword_index or TfidfIndex()
        self._graph_index = graph_index or Neo4jGraphIndex()

    def index(
        self,
        *,
        storage_type: str,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str | None:
        if storage_type == STORAGE_TYPE_VECTOR:
            return self._vector_index.upsert_chunks(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
        if storage_type == STORAGE_TYPE_KEYWORD:
            return self._keyword_index.save(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
        if storage_type == STORAGE_TYPE_GRAPH:
            self._graph_index.index_chunks(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
            return None

        raise ValueError(f"Unsupported storage_type: {storage_type}")
