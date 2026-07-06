from unittest.mock import MagicMock, patch

from llama_index.core.schema import NodeWithScore, TextNode

from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.infrastructure.ai.llamaindex.retriever_factory import RetrieverFactory


def test_retriever_factory_returns_empty_when_collection_missing() -> None:
    qdrant = MagicMock()
    qdrant._get_client.return_value.collection_exists.return_value = False
    factory = RetrieverFactory(qdrant=qdrant, embed_model=MagicMock())

    hits = factory.retrieve_vector(
        organization_id="org-1",
        knowledgebase_id="kb-1",
        query="refund policy",
    )

    assert hits == []


def test_retriever_factory_maps_retrieved_vector_nodes() -> None:
    qdrant = MagicMock()
    qdrant._get_client.return_value.collection_exists.return_value = True
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        NodeWithScore(
            node=TextNode(text="Refund within 30 days.", metadata={"chunk_id": "c1"}),
            score=0.92,
        ),
    ]
    index = MagicMock()
    index.as_retriever.return_value = retriever
    factory = RetrieverFactory(qdrant=qdrant, embed_model=MagicMock())

    with patch(
        "app.infrastructure.ai.llamaindex.retriever_factory.VectorStoreIndex.from_vector_store",
        return_value=index,
    ):
        with patch("app.infrastructure.ai.llamaindex.retriever_factory.build_qdrant_vector_store"):
            hits = factory.retrieve_vector(
                organization_id="org-1",
                knowledgebase_id="kb-1",
                query="refund policy",
                min_score=0.7,
            )

    assert len(hits) == 1
    assert hits[0]["text"] == "Refund within 30 days."
    assert hits[0]["chunk_id"] == "c1"
    assert hits[0]["score"] == 0.92


def test_retriever_factory_keyword_path() -> None:
    factory = RetrieverFactory(qdrant=MagicMock(), embed_model=MagicMock())
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        NodeWithScore(
            node=TextNode(text="payment refund policy", metadata={"chunk_id": "k1"}),
            score=0.2,
        ),
    ]

    with patch("app.infrastructure.ai.llamaindex.retriever_factory.keyword_index_dir") as index_dir:
        index_dir.return_value.exists.return_value = True
        with patch("app.infrastructure.ai.llamaindex.retriever_factory.BM25Retriever") as bm25_cls:
            bm25_cls.from_persist_dir.return_value = retriever
            hits = factory.retrieve_keyword(
                organization_id="org-1",
                knowledgebase_id="kb-1",
                query="refund",
            )

    assert hits[0]["text"] == "payment refund policy"
    assert hits[0]["chunk_id"] == "k1"


def test_retriever_factory_graph_path() -> None:
    factory = RetrieverFactory(qdrant=MagicMock(), embed_model=MagicMock())
    graph_store = MagicMock()
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        NodeWithScore(
            node=TextNode(
                text="Acme Corp owns Example Bank.",
                metadata={"chunk_id": "g1", "knowledgebase_id": "kb-1"},
            ),
            score=0.5,
        ),
    ]
    index = MagicMock()
    index.as_retriever.return_value = retriever

    with patch("app.infrastructure.ai.llamaindex.retriever_factory.graph_index_marker") as marker:
        marker.return_value.exists.return_value = True
        with patch(
            "app.infrastructure.ai.llamaindex.retriever_factory.build_neo4j_property_graph_store",
            return_value=graph_store,
        ):
            with patch(
                "app.infrastructure.ai.llamaindex.retriever_factory.PropertyGraphIndex.from_existing",
                return_value=index,
            ):
                hits = factory.retrieve_graph(
                    organization_id="org-1",
                    knowledgebase_id="kb-1",
                    query="who owns the bank",
                )

    assert hits[0]["text"] == "Acme Corp owns Example Bank."
    graph_store.close.assert_called_once()


def test_retriever_factory_search_dispatches_by_storage_type() -> None:
    factory = RetrieverFactory(qdrant=MagicMock(), embed_model=MagicMock())
    factory.retrieve_vector = MagicMock(return_value=[{"text": "vector"}])
    factory.retrieve_keyword = MagicMock(return_value=[{"text": "keyword"}])
    factory.retrieve_graph = MagicMock(return_value=[{"text": "graph"}])

    assert factory.search(
        storage_type=STORAGE_TYPE_VECTOR,
        organization_id="org-1",
        knowledgebase_id="kb-1",
        query="q",
    ) == [{"text": "vector"}]
    assert factory.search(
        storage_type=STORAGE_TYPE_KEYWORD,
        organization_id="org-1",
        knowledgebase_id="kb-1",
        query="q",
    ) == [{"text": "keyword"}]
    assert factory.search(
        storage_type=STORAGE_TYPE_GRAPH,
        organization_id="org-1",
        knowledgebase_id="kb-1",
        query="q",
    ) == [{"text": "graph"}]
