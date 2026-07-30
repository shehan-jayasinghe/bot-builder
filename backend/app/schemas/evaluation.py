from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvalMode(StrEnum):
    FULL_BOT = "full_bot"
    RAG_ONLY = "rag_only"


class EvalRunStatus(StrEnum):
    COMPLETE = "complete"
    FAILED = "failed"


class EvalScores(BaseModel):
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None


class EvalThresholds(BaseModel):
    faithfulness: float
    context_precision: float


class EvalRunRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    ground_truth: str | None = Field(default=None, max_length=8000)
    mode: EvalMode = EvalMode.FULL_BOT
    knowledge_base_names: list[str] | None = None
    sender_id: str | None = Field(default=None, min_length=1, max_length=200)


class EvalRunSummary(BaseModel):
    run_id: str
    question: str | None = None
    mode: EvalMode
    status: EvalRunStatus
    scores: EvalScores
    thresholds: EvalThresholds
    passed: bool
    created_at: datetime | None = None


class EvalRunResponse(BaseModel):
    run_id: str
    status: EvalRunStatus
    scores: EvalScores
    thresholds: EvalThresholds
    passed: bool


class EvalRunListResponse(BaseModel):
    items: list[EvalRunSummary]
    total: int


class EvalRunDetailResponse(BaseModel):
    run_id: str
    agent_id: str
    question: str
    ground_truth: str | None = None
    mode: EvalMode
    status: EvalRunStatus
    turn_evidence: dict[str, Any]
    scores: EvalScores
    thresholds: EvalThresholds
    passed: bool
    faithfulness_detail: dict[str, Any] | None = None
    answer_relevancy_detail: dict[str, Any] | None = None
    context_precision_detail: dict[str, Any] | None = None
    context_recall_detail: dict[str, Any] | None = None
    created_at: datetime


class EvalDatasetCase(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    ground_truth: str | None = Field(default=None, max_length=8000)
    knowledge_base_names: list[str] | None = None


class EvalDatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cases: list[EvalDatasetCase] = Field(min_length=1)


class EvalDatasetResponse(BaseModel):
    dataset_id: str
    name: str
    case_count: int


class EvalDatasetListItem(BaseModel):
    dataset_id: str
    name: str
    source: str
    case_count: int


class EvalDatasetListResponse(BaseModel):
    items: list[EvalDatasetListItem]


class EvalDummyDatasetResponse(BaseModel):
    name: str
    industry: str
    agent_type: str
    cases: list[EvalDatasetCase]
