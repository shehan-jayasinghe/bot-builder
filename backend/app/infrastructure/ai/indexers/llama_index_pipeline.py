import logging

from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.domain.models.source_document import ChunkDocument
from app.infrastructure.ai.llamaindex.index_factory import IndexFactory

logger = logging.getLogger(__name__)


class LlamaIndexPipeline:
    """Route indexing by storage_type (vector, keyword, graph)."""

    def __init__(
        self,
        *,
        index_factory: IndexFactory | None = None,
    ) -> None:
        self._index_factory = index_factory or IndexFactory()

    def index(
        self,
        *,
        storage_type: str,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str | None:
        if storage_type not in {
            STORAGE_TYPE_VECTOR,
            STORAGE_TYPE_KEYWORD,
            STORAGE_TYPE_GRAPH,
        }:
            raise ValueError(f"Unsupported storage_type: {storage_type}")
        return self._index_factory.index(
            storage_type=storage_type,
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
            chunks=chunks,
        )
