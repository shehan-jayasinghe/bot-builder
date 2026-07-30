from unittest.mock import MagicMock, patch

from app.domain.models.source_document import ChunkDocument
from app.infrastructure.ai.llamaindex.keyword_qdrant import (
    _build_sparse_vector,
    _tokenize,
    search_keyword_sparse,
    upsert_keyword_chunks,
)


def test_tokenize_lowercases_and_splits() -> None:
    tokens = _tokenize("Hello World 123 foo-bar")
    assert tokens == ["hello", "world", "123", "foo", "bar"]


def test_tokenize_empty_string() -> None:
    assert _tokenize("") == []


def test_build_sparse_vector_has_indices_and_values() -> None:
    sparse = _build_sparse_vector(["hello", "world", "hello"])
    assert len(sparse.indices) == 2
    assert len(sparse.values) == 2
    assert all(v > 0 for v in sparse.values)


def test_upsert_keyword_chunks_creates_collection_and_upserts() -> None:
    qdrant = MagicMock()
    client = qdrant._get_client.return_value
    client.collection_exists.return_value = False

    chunks = [
        ChunkDocument(chunk_id="k1", text="payment refund policy", token_count=3, metadata={}),
        ChunkDocument(chunk_id="k2", text="shipping returns", token_count=2, metadata={}),
    ]

    upsert_keyword_chunks(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        chunks=chunks,
        organization_id="org-1",
        knowledgebase_id="kb-1",
    )

    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
    points = client.upsert.call_args.kwargs["points"]
    assert len(points) == 2
    assert points[0].payload["chunk_id"] == "k1"
    assert points[0].payload["text"] == "payment refund policy"


def test_upsert_keyword_chunks_skips_empty_text() -> None:
    qdrant = MagicMock()
    client = qdrant._get_client.return_value
    client.collection_exists.return_value = True

    chunks = [
        ChunkDocument(chunk_id="k1", text="   ", token_count=0, metadata={}),
    ]

    upsert_keyword_chunks(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        chunks=chunks,
        organization_id="org-1",
        knowledgebase_id="kb-1",
    )

    client.upsert.assert_not_called()


def test_search_keyword_sparse_returns_hits() -> None:
    qdrant = MagicMock()
    client = qdrant._get_client.return_value
    client.collection_exists.return_value = True

    hit = MagicMock()
    hit.score = 1.5
    hit.payload = {"text": "payment refund policy", "chunk_id": "k1"}
    client.query_points.return_value.points = [hit]

    results = search_keyword_sparse(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        query="refund",
        top_k=5,
    )

    assert len(results) == 1
    assert results[0]["text"] == "payment refund policy"
    assert results[0]["chunk_id"] == "k1"
    assert results[0]["score"] == 1.5


def test_search_keyword_sparse_returns_empty_when_no_collection() -> None:
    qdrant = MagicMock()
    client = qdrant._get_client.return_value
    client.collection_exists.return_value = False

    results = search_keyword_sparse(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        query="refund",
    )

    assert results == []


def test_search_keyword_sparse_returns_empty_for_empty_query() -> None:
    qdrant = MagicMock()
    client = qdrant._get_client.return_value
    client.collection_exists.return_value = True

    results = search_keyword_sparse(
        qdrant=qdrant,
        collection_name="kb_org-1_kb-1",
        query="   ",
    )

    assert results == []
