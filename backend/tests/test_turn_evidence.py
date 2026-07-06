import asyncio
from unittest.mock import AsyncMock

from app.domain.graph.langchain.tool_router import run_search_knowledge_tool
from app.domain.graph.search_knowledge_delegate import SEARCH_KNOWLEDGE_TOOL_NAME
from app.domain.graph.turn_evidence import TurnEvidence
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.rag_result import RagChunk, RagRetrieveResult
from app.domain.pipeline.rag.retriever import RAGRetriever

ORG_ID = "6a3b7c61d8139334274fbbfc"


def test_turn_evidence_records_rag_retrieval() -> None:
    evidence = TurnEvidence(user_message="What is the minimum balance?")
    chunks = [
        RagChunk(
            text="Min balance ₹10,000 urban",
            rank=1,
            score=0.91,
            chunk_id="c1",
            kb_id="kb-1",
            kb_name="FAQ",
        ),
    ]
    evidence.record_rag_retrieval(query="minimum balance", chunks=chunks)
    evidence.record_tool_call(
        name=SEARCH_KNOWLEDGE_TOOL_NAME,
        arguments={"query": "minimum balance"},
        status="complete",
    )
    evidence.set_assistant_replies(["Urban minimum is ₹10,000."])
    evidence.set_routing({"mode": "orchestrator"})

    data = evidence.to_dict()
    assert data["user_message"] == "What is the minimum balance?"
    assert len(data["rag_retrievals"]) == 1
    assert data["rag_retrievals"][0]["query"] == "minimum balance"
    assert data["rag_retrievals"][0]["chunks"][0]["rank"] == 1
    assert data["rag_retrievals"][0]["chunks"][0]["text"] == "Min balance ₹10,000 urban"
    assert data["assistant_replies"] == ["Urban minimum is ₹10,000."]
    assert data["routing"]["mode"] == "orchestrator"


def test_rag_retriever_returns_ranked_chunks() -> None:
    async def _run() -> None:
        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        retriever = RAGRetriever()
        retriever._search_kb = AsyncMock(  # type: ignore[method-assign]
            return_value=[
                {"text": "chunk one", "score": 0.9, "chunk_id": "a"},
                {"text": "chunk two", "score": 0.8, "chunk_id": "b"},
            ],
        )

        result = await retriever.retrieve(
            query="policy",
            knowledge_bases=[kb],
            organization_id=ORG_ID,
        )

        assert result.chunk_count == 2
        assert len(result.chunks) == 2
        assert result.chunks[0].rank == 1
        assert result.chunks[1].rank == 2
        assert result.chunks[0].kb_id == "kb-1"
        assert result.chunks[0].kb_name == "FAQ"

    asyncio.run(_run())


def test_search_knowledge_records_turn_evidence_and_trace_chunks() -> None:
    async def _run() -> None:
        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        rag = AsyncMock()
        rag.retrieve.return_value = RagRetrieveResult(
            context="### FAQ\n- refund within 30 days",
            kb_ids=["kb-1"],
            chunk_count=1,
            storage_types=["vector"],
            chunks=[
                RagChunk(
                    text="refund within 30 days",
                    rank=1,
                    score=0.88,
                    chunk_id="c1",
                    kb_id="kb-1",
                    kb_name="FAQ",
                ),
            ],
        )
        evidence = TurnEvidence(user_message="refund policy?")
        trace_events: list[tuple[str, dict]] = []

        async def trace(event: str, data: dict) -> None:
            trace_events.append((event, data))

        await run_search_knowledge_tool(
            tool_args={"query": "refund policy"},
            knowledge_bases=[kb],
            organization_id=ORG_ID,
            rag=rag,
            trace=trace,
            turn_evidence=evidence,
        )

        data = evidence.to_dict()
        assert len(data["rag_retrievals"]) == 1
        assert data["rag_retrievals"][0]["chunks"][0]["text"] == "refund within 30 days"
        tool_complete = next(payload for event, payload in trace_events if event == "tool_complete")
        assert tool_complete["query"] == "refund policy"
        assert tool_complete["chunks"][0]["rank"] == 1

    asyncio.run(_run())
