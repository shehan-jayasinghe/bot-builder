from __future__ import annotations

import asyncio
import math
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.domain.evaluation.metric_breakdown import build_metric_breakdown
from app.domain.evaluation.ragas_runner import (
    RagasRunner,
    _scores_from_result,
    answer_from_turn_evidence,
    contexts_from_turn_evidence,
)


def test_contexts_from_turn_evidence_flattens_chunks() -> None:
    evidence = {
        "rag_retrievals": [
            {
                "query": "balance",
                "chunks": [
                    {"rank": 1, "text": "Urban min ₹10,000"},
                    {"rank": 2, "text": "Rural min ₹2,500"},
                ],
            },
        ],
    }
    assert contexts_from_turn_evidence(evidence) == [
        "Urban min ₹10,000",
        "Rural min ₹2,500",
    ]


def test_answer_from_turn_evidence_joins_replies() -> None:
    evidence = {"assistant_replies": ["Line one", "Line two"]}
    assert answer_from_turn_evidence(evidence) == "Line one\nLine two"


def test_scores_from_result_handles_nan() -> None:
    result = SimpleNamespace(_repr_dict={"faithfulness": 0.8, "answer_relevancy": math.nan})
    scores = _scores_from_result(result)
    assert scores["faithfulness"] == 0.8
    assert scores["answer_relevancy"] is None


def test_build_metric_breakdown_includes_precision_at_k() -> None:
    evidence = {
        "rag_retrievals": [
            {
                "query": "balance",
                "chunks": [
                    {"rank": 1, "text": "Urban min ₹10,000", "score": 0.91},
                    {"rank": 2, "text": "Noise chunk", "score": 0.2},
                ],
            },
        ],
    }
    breakdown = build_metric_breakdown(
        turn_evidence=evidence,
        scores={
            "faithfulness": 0.75,
            "answer_relevancy": 0.9,
            "context_precision": 0.8,
            "context_recall": 0.7,
        },
        ground_truth="Urban minimum ₹10,000",
        faithfulness_detail={"claims": [], "score": 0.75},
    )
    assert breakdown["context_precision_detail"]["precision_at_k"] == [1.0, 0.5]
    assert len(breakdown["context_recall_detail"]["reference_claims"]) == 1


def test_ragas_runner_run_uses_injected_dependencies() -> None:
    async def _run() -> None:
        mock_result = SimpleNamespace(
            _repr_dict={
                "faithfulness": 0.9,
                "answer_relevancy": 0.85,
                "context_precision": None,
                "context_recall": None,
            },
            traces=[],
        )

        async def fake_aevaluate(**_kwargs):
            return mock_result

        runner = RagasRunner(llm_wrapper=MagicMock(), embeddings_wrapper=MagicMock())
        runner._build_faithfulness_detail = AsyncMock(return_value={"claims": [], "score": 0.9})

        import app.domain.evaluation.ragas_runner as module

        original = module.aevaluate
        module.aevaluate = fake_aevaluate
        try:
            result = await runner.run(
                question="What is the minimum balance?",
                answer="Urban minimum is ₹10,000.",
                contexts=["Urban min ₹10,000"],
                ground_truth=None,
            )
        finally:
            module.aevaluate = original

        assert result.scores["faithfulness"] == 0.9
        assert result.scores["context_precision"] is None

    asyncio.run(_run())
