from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from ragas import aevaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.metrics._faithfulness import Faithfulness

from app.infrastructure.ai.ragas_llm import build_ragas_embeddings, build_ragas_judge_llm

logger = logging.getLogger(__name__)

METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)


@dataclass
class RagasRunResult:
    scores: dict[str, float | None]
    traces: list[dict[str, Any]] = field(default_factory=list)
    faithfulness_detail: dict[str, Any] | None = None


def contexts_from_turn_evidence(turn_evidence: dict[str, Any]) -> list[str]:
    contexts: list[str] = []
    for retrieval in turn_evidence.get("rag_retrievals", []):
        for chunk in retrieval.get("chunks", []):
            text = str(chunk.get("text", "")).strip()
            if text:
                contexts.append(text)
    return contexts


def answer_from_turn_evidence(turn_evidence: dict[str, Any]) -> str:
    replies = turn_evidence.get("assistant_replies") or []
    parts = [str(reply).strip() for reply in replies if str(reply).strip()]
    return "\n".join(parts)


class RagasRunner:
    def __init__(
        self,
        *,
        llm_wrapper=None,
        embeddings_wrapper=None,
    ) -> None:
        self._llm_wrapper = llm_wrapper
        self._embeddings_wrapper = embeddings_wrapper

    def _llm(self):
        if self._llm_wrapper is None:
            self._llm_wrapper = build_ragas_judge_llm()
        return self._llm_wrapper

    def _embeddings(self):
        if self._embeddings_wrapper is None:
            self._embeddings_wrapper = build_ragas_embeddings()
        return self._embeddings_wrapper

    async def run(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> RagasRunResult:
        sample = SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=contexts or [""],
            reference=ground_truth,
        )
        dataset = EvaluationDataset(samples=[sample])

        metrics: list[Any] = [faithfulness, answer_relevancy]
        if ground_truth:
            metrics.extend([context_precision, context_recall])

        result = await aevaluate(
            dataset=dataset,
            metrics=metrics,
            llm=self._llm(),
            embeddings=self._embeddings(),
            show_progress=False,
            raise_exceptions=False,
        )

        scores = _scores_from_result(result)
        faithfulness_detail = await self._build_faithfulness_detail(
            question=question,
            answer=answer,
            contexts=contexts,
            score=scores.get("faithfulness"),
        )
        return RagasRunResult(
            scores=scores,
            traces=list(result.traces or []),
            faithfulness_detail=faithfulness_detail,
        )

    async def _build_faithfulness_detail(
        self,
        *,
        question: str,
        answer: str,
        contexts: list[str],
        score: float | None,
    ) -> dict[str, Any] | None:
        if not answer.strip():
            return {"claims": [], "score": score}

        metric = Faithfulness(llm=self._llm())
        row = {
            "user_input": question,
            "response": answer,
            "retrieved_contexts": contexts or [""],
        }
        try:
            statements = await metric._create_statements(row, callbacks=None)
            if not statements.statements:
                return {"claims": [], "score": score}
            verdicts = await metric._create_verdicts(row, statements.statements, callbacks=None)
            claims = [
                {
                    "text": item.statement,
                    "verdict": "grounded" if item.verdict else "hallucinated",
                    "source_chunk_index": None,
                }
                for item in verdicts.statements
            ]
            computed = float(metric._compute_score(verdicts))
            if math.isnan(computed):
                computed = score
            return {"claims": claims, "score": computed if score is None else score}
        except Exception:
            logger.exception("Failed to build faithfulness detail")
            return {"claims": [], "score": score}


def _scores_from_result(result: Any) -> dict[str, float | None]:
    scores: dict[str, float | None] = {name: None for name in METRIC_NAMES}
    for name in METRIC_NAMES:
        value = result._repr_dict.get(name)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            scores[name] = None
        else:
            scores[name] = float(value)
    return scores
