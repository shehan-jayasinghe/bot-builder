import asyncio
from unittest.mock import MagicMock

from app.domain.constants.knowledgebase_constants import STORAGE_TYPE_KEYWORD, STORAGE_TYPE_VECTOR
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.retriever import RAGRetriever, format_rag_context

ORG_ID = "6a3b7c61d8139334274fbbfc"
KB_VECTOR_ID = "6a3f9012d8139334274fbc01"
KB_KEYWORD_ID = "6a3f9012d8139334274fbc02"
KB_GRAPH_ID = "6a3f9012d8139334274fbc03"


def test_format_rag_context_groups_by_kb_name() -> None:
    context = format_rag_context(
        {
            "Policy docs": ["Refund within 30 days.", "No cash refunds."],
            "FAQ": ["Hours are 9-5."],
        },
    )
    assert "### Policy docs" in context
    assert "Refund within 30 days." in context
    assert "### FAQ" in context


def test_rag_retriever_returns_empty_without_knowledge_bases() -> None:
    async def _run() -> None:
        retriever = RAGRetriever()
        result = await retriever.retrieve(
            query="payment policy",
            knowledge_bases=[],
            organization_id=ORG_ID,
        )
        assert result.context == ""
        assert result.chunk_count == 0

    asyncio.run(_run())


def test_rag_retriever_vector_path() -> None:
    async def _run() -> None:
        retriever_factory = MagicMock()
        retriever_factory.search.return_value = [
            {"text": "Vector chunk one.", "score": 0.91, "chunk_id": "c1"},
            {"text": "Vector chunk two.", "score": 0.82, "chunk_id": "c2"},
        ]

        retriever = RAGRetriever(retriever_factory=retriever_factory)
        result = await retriever.retrieve(
            query="refund policy",
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id=KB_VECTOR_ID,
                    name="Policy docs",
                    storage_type=STORAGE_TYPE_VECTOR,
                    status="ready",
                ),
            ],
            organization_id=ORG_ID,
        )

        assert "Vector chunk one." in result.context
        assert result.chunk_count == 2
        assert result.kb_ids == [KB_VECTOR_ID]
        assert result.storage_types == [STORAGE_TYPE_VECTOR]
        retriever_factory.search.assert_called_once()

    asyncio.run(_run())


def test_rag_retriever_keyword_path() -> None:
    async def _run() -> None:
        retriever_factory = MagicMock()
        retriever_factory.search.return_value = [
            {"text": "Keyword snippet.", "score": 0.44, "chunk_id": "k1"},
        ]

        retriever = RAGRetriever(retriever_factory=retriever_factory)
        result = await retriever.retrieve(
            query="account number",
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id=KB_KEYWORD_ID,
                    name="FAQ",
                    storage_type=STORAGE_TYPE_KEYWORD,
                    status="ready",
                ),
            ],
            organization_id=ORG_ID,
        )

        assert "Keyword snippet." in result.context
        assert result.chunk_count == 1
        retriever_factory.search.assert_called_once()

    asyncio.run(_run())


def test_rag_retriever_merges_multiple_kbs_and_dedupes() -> None:
    async def _run() -> None:
        retriever_factory = MagicMock()

        def _search(**kwargs: object) -> list[dict[str, object]]:
            if kwargs["storage_type"] == STORAGE_TYPE_VECTOR:
                return [{"text": "Shared chunk.", "score": 0.9, "chunk_id": "c1"}]
            return [
                {"text": "Shared chunk.", "score": 0.5, "chunk_id": "k1"},
                {"text": "Unique keyword chunk.", "score": 0.4, "chunk_id": "k2"},
            ]

        retriever_factory.search.side_effect = _search

        retriever = RAGRetriever(retriever_factory=retriever_factory)
        result = await retriever.retrieve(
            query="policy",
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id=KB_VECTOR_ID,
                    name="Vector KB",
                    storage_type=STORAGE_TYPE_VECTOR,
                    status="ready",
                ),
                RuntimeKnowledgeBase(
                    id=KB_KEYWORD_ID,
                    name="Keyword KB",
                    storage_type=STORAGE_TYPE_KEYWORD,
                    status="ready",
                ),
            ],
            organization_id=ORG_ID,
        )

        assert result.chunk_count == 2
        assert result.context.count("Shared chunk.") == 1
        assert "Unique keyword chunk." in result.context

    asyncio.run(_run())


def test_rag_retriever_degrades_on_search_error() -> None:
    async def _run() -> None:
        retriever_factory = MagicMock()
        retriever_factory.search.side_effect = RuntimeError("Qdrant unavailable")
        retriever = RAGRetriever(retriever_factory=retriever_factory)

        result = await retriever.retrieve(
            query="policy",
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id=KB_VECTOR_ID,
                    name="Policy docs",
                    storage_type=STORAGE_TYPE_VECTOR,
                    status="ready",
                ),
            ],
            organization_id=ORG_ID,
        )

        assert result.context == ""
        assert result.error is not None
        assert "Qdrant unavailable" in result.error

    asyncio.run(_run())
