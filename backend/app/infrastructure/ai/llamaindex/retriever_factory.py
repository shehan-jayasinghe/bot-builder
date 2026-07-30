import logging
from typing import Any

from llama_index.core import PropertyGraphIndex, VectorStoreIndex

from app.config import settings
from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.infrastructure.ai.llamaindex.bedrock_embedding import BedrockLlamaEmbedding
from app.infrastructure.ai.llamaindex.collection_naming import kb_collection_name
from app.infrastructure.ai.llamaindex.constants import (
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    GRAPH_MIN_SCORE,
    KEYWORD_MIN_SCORE,
)
from app.infrastructure.ai.llamaindex.graph_store import build_neo4j_property_graph_store
from app.infrastructure.ai.llamaindex.index_factory import build_qdrant_vector_store
from app.infrastructure.ai.llamaindex.keyword_qdrant import search_keyword_sparse
from app.infrastructure.ai.llamaindex.node_mapping import hits_from_nodes
from app.infrastructure.ai.llamaindex.persistence import graph_index_marker
from app.infrastructure.connectors.qdrant.qdrant_connector import QdrantConnector

logger = logging.getLogger(__name__)


class RetrieverFactory:
    def __init__(
        self,
        *,
        qdrant: QdrantConnector | None = None,
        embed_model: BedrockLlamaEmbedding | None = None,
    ) -> None:
        self._qdrant = qdrant or QdrantConnector(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._embed_model = embed_model or BedrockLlamaEmbedding()

    def search(
        self,
        *,
        storage_type: str,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict[str, Any]]:
        if storage_type == STORAGE_TYPE_VECTOR:
            return self.retrieve_vector(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                query=query,
                top_k=top_k,
                min_score=DEFAULT_MIN_SCORE,
            )
        if storage_type == STORAGE_TYPE_KEYWORD:
            return self.retrieve_keyword(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                query=query,
                top_k=top_k,
            )
        if storage_type == STORAGE_TYPE_GRAPH:
            return self.retrieve_graph(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                query=query,
                top_k=top_k,
            )
        raise ValueError(f"Unsupported storage_type: {storage_type}")

    def retrieve_vector(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> list[dict[str, Any]]:
        collection_name = kb_collection_name(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        client = self._qdrant._get_client()
        if not client.collection_exists(collection_name):
            logger.info("Qdrant collection missing for knowledgebase_id=%s", knowledgebase_id)
            return []

        vector_store = build_qdrant_vector_store(
            collection_name=collection_name,
            qdrant=self._qdrant,
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self._embed_model,
        )
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        return hits_from_nodes(nodes, min_score=min_score)

    def retrieve_keyword(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict[str, Any]]:
        collection_name = kb_collection_name(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        return search_keyword_sparse(
            qdrant=self._qdrant,
            collection_name=collection_name,
            query=query,
            top_k=top_k,
            min_score=KEYWORD_MIN_SCORE,
        )

    def retrieve_graph(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict[str, Any]]:
        marker = graph_index_marker(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        if not marker.exists():
            logger.info("Graph index marker missing for knowledgebase_id=%s", knowledgebase_id)
            return []

        graph_store = build_neo4j_property_graph_store()
        try:
            index = PropertyGraphIndex.from_existing(
                property_graph_store=graph_store,
                embed_model=self._embed_model,
                use_async=False,
                show_progress=False,
            )
            retriever = index.as_retriever(include_text=True, similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
        finally:
            graph_store.close()

        scoped_nodes = [
            item
            for item in nodes
            if _node_matches_kb(item, knowledgebase_id=knowledgebase_id)
        ]
        return hits_from_nodes(scoped_nodes, min_score=GRAPH_MIN_SCORE)


def _node_matches_kb(item: Any, *, knowledgebase_id: str) -> bool:
    kb_id = str(item.node.metadata.get("knowledgebase_id", ""))
    if not kb_id:
        return True
    return kb_id == knowledgebase_id
