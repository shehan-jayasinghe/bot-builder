import asyncio
from unittest.mock import MagicMock

from app.domain.constants.knowledgebase_constants import STORAGE_TYPE_KEYWORD, STORAGE_TYPE_VECTOR
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.models.source_document import ChunkDocument
from app.domain.pipeline.rag.keyword_search import KeywordSearchHit
from app.domain.pipeline.rag.retriever import RAGRetriever, format_rag_context
from app.domain.pipeline.rag.vector_search import VectorSearchHit
from app.infrastructure.keyword.tfidf_index import TfidfIndex

ORG_ID = "6a3b7c61d8139334274fbbfc"
KB_VECTOR_ID = "6a3f9012d8139334274fbc01"
KB_KEYWORD_ID = "6a3f9012d8139334274fbc02"


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
        vector_search = MagicMock()
        vector_search.search.return_value = [
            VectorSearchHit(text="Vector chunk one.", score=0.91, chunk_id="c1"),
            VectorSearchHit(text="Vector chunk two.", score=0.82, chunk_id="c2"),
        ]
        keyword_search = MagicMock()

        retriever = RAGRetriever(vector_search=vector_search, keyword_search=keyword_search)
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
        vector_search.search.assert_called_once()

    asyncio.run(_run())


def test_rag_retriever_keyword_path() -> None:
    async def _run() -> None:
        vector_search = MagicMock()
        keyword_search = MagicMock()
        keyword_search.search.return_value = [
            KeywordSearchHit(text="Keyword snippet.", score=0.44, chunk_id="k1"),
        ]

        retriever = RAGRetriever(vector_search=vector_search, keyword_search=keyword_search)
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
        keyword_search.search.assert_called_once()

    asyncio.run(_run())


def test_rag_retriever_merges_multiple_kbs_and_dedupes() -> None:
    async def _run() -> None:
        vector_search = MagicMock()
        vector_search.search.return_value = [
            VectorSearchHit(text="Shared chunk.", score=0.9, chunk_id="c1"),
        ]
        keyword_search = MagicMock()
        keyword_search.search.return_value = [
            KeywordSearchHit(text="Shared chunk.", score=0.5, chunk_id="k1"),
            KeywordSearchHit(text="Unique keyword chunk.", score=0.4, chunk_id="k2"),
        ]

        retriever = RAGRetriever(vector_search=vector_search, keyword_search=keyword_search)
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
        vector_search = MagicMock()
        vector_search.search.side_effect = RuntimeError("Qdrant unavailable")
        retriever = RAGRetriever(vector_search=vector_search, keyword_search=MagicMock())

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


def test_tfidf_index_search_returns_ranked_hits(tmp_path) -> None:
    index = TfidfIndex(base_dir=str(tmp_path))
    index.save(
        organization_id=ORG_ID,
        knowledgebase_id=KB_KEYWORD_ID,
        chunks=[
            ChunkDocument(chunk_id="1", text="payment refund policy", token_count=3, metadata={}),
            ChunkDocument(chunk_id="2", text="office opening hours", token_count=3, metadata={}),
        ],
    )

    hits = index.search(
        organization_id=ORG_ID,
        knowledgebase_id=KB_KEYWORD_ID,
        query="refund payment",
        top_k=2,
    )

    assert hits
    assert "payment refund policy" in hits[0]["text"]
