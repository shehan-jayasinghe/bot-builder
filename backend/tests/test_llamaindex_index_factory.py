from unittest.mock import MagicMock, patch

from app.domain.models.source_document import ChunkDocument
from app.infrastructure.ai.llamaindex.index_factory import IndexFactory


def test_index_factory_indexes_vector_chunks() -> None:
    factory = IndexFactory(
        qdrant=MagicMock(),
        embed_model=MagicMock(),
    )
    chunks = [
        ChunkDocument(chunk_id="c1", text="Refund within 30 days.", token_count=4, metadata={}),
    ]

    with patch("app.infrastructure.ai.llamaindex.index_factory.VectorStoreIndex") as index_cls:
        with patch("app.infrastructure.ai.llamaindex.index_factory.build_qdrant_vector_store"):
            collection = factory.index_vector(
                organization_id="org-1",
                knowledgebase_id="kb-1",
                chunks=chunks,
            )

    assert collection == "kb_org-1_kb-1"
    index_cls.assert_called_once()
    nodes = index_cls.call_args.args[0]
    assert len(nodes) == 1
    assert nodes[0].metadata["chunk_id"] == "c1"


def test_index_factory_returns_collection_name_for_empty_chunks() -> None:
    factory = IndexFactory(qdrant=MagicMock(), embed_model=MagicMock())

    with patch("app.infrastructure.ai.llamaindex.index_factory.VectorStoreIndex") as index_cls:
        collection = factory.index_vector(
            organization_id="org-1",
            knowledgebase_id="kb-1",
            chunks=[],
        )

    assert collection == "kb_org-1_kb-1"
    index_cls.assert_not_called()


def test_index_factory_indexes_keyword_chunks() -> None:
    qdrant = MagicMock()
    factory = IndexFactory(qdrant=qdrant, embed_model=MagicMock())
    chunks = [
        ChunkDocument(chunk_id="k1", text="payment refund policy", token_count=3, metadata={}),
    ]

    with patch("app.infrastructure.ai.llamaindex.index_factory.upsert_keyword_chunks") as upsert:
        collection = factory.index_keyword(
            organization_id="org-1",
            knowledgebase_id="kb-1",
            chunks=chunks,
        )

    assert collection == "kb_org-1_kb-1"
    upsert.assert_called_once_with(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        chunks=chunks,
        organization_id="org-1",
        knowledgebase_id="kb-1",
    )


def test_index_factory_indexes_graph_chunks() -> None:
    factory = IndexFactory(
        qdrant=MagicMock(),
        embed_model=MagicMock(),
    )
    chunks = [
        ChunkDocument(chunk_id="g1", text="Acme Corp owns Example Bank.", token_count=5, metadata={}),
    ]
    graph_store = MagicMock()

    with patch("app.infrastructure.ai.llamaindex.index_factory.build_neo4j_property_graph_store", return_value=graph_store):
        with patch("app.infrastructure.ai.llamaindex.index_factory.SimpleLLMPathExtractor"):
            with patch("app.infrastructure.ai.llamaindex.index_factory.PropertyGraphIndex") as graph_index_cls:
                with patch("app.infrastructure.ai.llamaindex.index_factory.graph_index_marker") as marker:
                    marker_path = MagicMock()
                    marker.return_value = marker_path
                    factory.index_graph(
                        organization_id="org-1",
                        knowledgebase_id="kb-1",
                        chunks=chunks,
                    )

    graph_index_cls.assert_called_once()
    graph_store.close.assert_called_once()
    marker_path.parent.mkdir.assert_called_once()
    marker_path.write_text.assert_called_once()
