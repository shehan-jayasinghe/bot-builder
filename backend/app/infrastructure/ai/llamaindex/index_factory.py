import logging
import shutil

from llama_index.core import PropertyGraphIndex, StorageContext, VectorStoreIndex
from llama_index.core.indices.property_graph.transformations import SimpleLLMPathExtractor
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams

from app.config import settings
from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.domain.models.source_document import ChunkDocument
from app.infrastructure.ai.llamaindex.bedrock_embedding import BedrockLlamaEmbedding
from app.infrastructure.ai.llamaindex.bedrock_llm import BedrockLlamaLLM
from app.infrastructure.ai.llamaindex.chunk_nodes import chunks_to_text_nodes
from app.infrastructure.ai.llamaindex.collection_naming import kb_collection_name
from app.infrastructure.ai.llamaindex.graph_store import build_neo4j_property_graph_store
from app.infrastructure.ai.llamaindex.persistence import graph_index_marker, keyword_index_dir
from app.infrastructure.connectors.qdrant.qdrant_connector import QdrantConnector

logger = logging.getLogger(__name__)


def build_qdrant_vector_store(
    *,
    collection_name: str,
    qdrant: QdrantConnector | None = None,
) -> QdrantVectorStore:
    connector = qdrant or QdrantConnector(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    return QdrantVectorStore(
        collection_name=collection_name,
        client=connector._get_client(),
        text_key="text",
        dense_config=VectorParams(
            size=settings.bedrock_embed_dimensions,
            distance=Distance.COSINE,
        ),
    )


class IndexFactory:
    def __init__(
        self,
        *,
        qdrant: QdrantConnector | None = None,
        embed_model: BedrockLlamaEmbedding | None = None,
        llm: BedrockLlamaLLM | None = None,
    ) -> None:
        self._qdrant = qdrant or QdrantConnector(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._embed_model = embed_model or BedrockLlamaEmbedding()
        self._llm = llm or BedrockLlamaLLM()

    def index(
        self,
        *,
        storage_type: str,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str | None:
        if storage_type == STORAGE_TYPE_VECTOR:
            return self.index_vector(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
        if storage_type == STORAGE_TYPE_KEYWORD:
            return self.index_keyword(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
        if storage_type == STORAGE_TYPE_GRAPH:
            self.index_graph(
                organization_id=organization_id,
                knowledgebase_id=knowledgebase_id,
                chunks=chunks,
            )
            return None
        raise ValueError(f"Unsupported storage_type: {storage_type}")

    def index_vector(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str:
        collection_name = kb_collection_name(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        nodes = chunks_to_text_nodes(
            chunks=chunks,
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        if not nodes:
            return collection_name

        vector_store = build_qdrant_vector_store(
            collection_name=collection_name,
            qdrant=self._qdrant,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=self._embed_model,
            show_progress=False,
        )
        logger.info(
            "Indexed %s vectors to Qdrant collection %s via LlamaIndex",
            len(nodes),
            collection_name,
        )
        return collection_name

    def index_keyword(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str:
        target_dir = keyword_index_dir(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        nodes = chunks_to_text_nodes(
            chunks=chunks,
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        if not nodes:
            return str(target_dir)

        retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=len(nodes),
        )
        retriever.persist(str(target_dir))
        logger.info(
            "Indexed %s keyword chunks to %s via LlamaIndex BM25",
            len(nodes),
            target_dir,
        )
        return str(target_dir)

    def index_graph(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> None:
        nodes = chunks_to_text_nodes(
            chunks=chunks,
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        if not nodes:
            return

        capped_nodes = nodes[: settings.rag_graph_max_chunks]
        graph_store = build_neo4j_property_graph_store()
        try:
            PropertyGraphIndex(
                capped_nodes,
                property_graph_store=graph_store,
                kg_extractors=[
                    SimpleLLMPathExtractor(
                        llm=self._llm,
                        num_workers=1,
                        max_paths_per_chunk=10,
                    ),
                ],
                embed_model=self._embed_model,
                embed_kg_nodes=True,
                use_async=False,
                show_progress=False,
            )
        finally:
            graph_store.close()

        marker = graph_index_marker(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("ready\n", encoding="utf-8")
        logger.info(
            "Indexed graph for knowledgebase_id=%s organization_id=%s (%s chunks)",
            knowledgebase_id,
            organization_id,
            len(capped_nodes),
        )
