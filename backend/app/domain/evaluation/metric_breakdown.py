from __future__ import annotations

import re
from typing import Any


def build_metric_breakdown(
  *,
  turn_evidence: dict[str, Any],
  scores: dict[str, float | None],
  ground_truth: str | None,
  faithfulness_detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
  contexts = _ranked_chunks(turn_evidence)
  return {
    "faithfulness_detail": faithfulness_detail or _default_faithfulness_detail(scores),
    "answer_relevancy_detail": _answer_relevancy_detail(scores),
    "context_precision_detail": _context_precision_detail(contexts, scores),
    "context_recall_detail": _context_recall_detail(contexts, ground_truth, scores),
  }


def _ranked_chunks(turn_evidence: dict[str, Any]) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for retrieval in turn_evidence.get("rag_retrievals", []):
    for chunk in retrieval.get("chunks", []):
      ranked.append(
        {
          "rank": chunk.get("rank", len(ranked) + 1),
          "text": chunk.get("text", ""),
          "score": chunk.get("score"),
          "kb_id": chunk.get("kb_id"),
        },
      )
  ranked.sort(key=lambda item: item.get("rank") or 0)
  return ranked


def _default_faithfulness_detail(scores: dict[str, float | None]) -> dict[str, Any]:
  return {"claims": [], "score": scores.get("faithfulness")}


def _answer_relevancy_detail(scores: dict[str, float | None]) -> dict[str, Any]:
  score = scores.get("answer_relevancy")
  return {
    "generated_questions": [],
    "similarities": [],
    "score": score,
  }


def _context_precision_detail(
  ranked_chunks: list[dict[str, Any]],
  scores: dict[str, float | None],
) -> dict[str, Any]:
  precision_at_k: list[float] = []
  relevant_so_far = 0
  for index, chunk in enumerate(ranked_chunks, start=1):
    label = "relevant" if chunk.get("score") is None or chunk.get("score", 0) >= 0.5 else "noise"
    if label == "relevant":
      relevant_so_far += 1
    precision_at_k.append(relevant_so_far / index)

  return {
    "ranked_chunks": [
      {
        "rank": chunk.get("rank", index + 1),
        "text": chunk.get("text", ""),
        "label": "relevant" if chunk.get("score") is None or chunk.get("score", 0) >= 0.5 else "noise",
      }
      for index, chunk in enumerate(ranked_chunks)
    ],
    "precision_at_k": precision_at_k,
    "score": scores.get("context_precision"),
  }


def _context_recall_detail(
  ranked_chunks: list[dict[str, Any]],
  ground_truth: str | None,
  scores: dict[str, float | None],
) -> dict[str, Any]:
  if not ground_truth:
    return {"reference_claims": [], "score": scores.get("context_recall")}

  claims = _split_claims(ground_truth)
  context_texts = [str(chunk.get("text", "")).lower() for chunk in ranked_chunks]
  reference_claims: list[dict[str, Any]] = []
  for claim in claims:
    claim_lower = claim.lower()
    chunk_index = next(
      (index for index, text in enumerate(context_texts) if _claim_supported(claim_lower, text)),
      None,
    )
    reference_claims.append(
      {
        "text": claim,
        "verdict": "supported" if chunk_index is not None else "missing",
        "chunk_index": chunk_index,
      },
    )

  return {
    "reference_claims": reference_claims,
    "score": scores.get("context_recall"),
  }


def _split_claims(text: str) -> list[str]:
  parts = re.split(r"[.;]\s+|\n+", text.strip())
  return [part.strip() for part in parts if part.strip()]


def _claim_supported(claim: str, context: str) -> bool:
  tokens = [token for token in re.findall(r"\w+", claim) if len(token) > 3]
  if not tokens:
    return claim in context
  hits = sum(1 for token in tokens if token in context)
  return hits >= max(1, len(tokens) // 2)
