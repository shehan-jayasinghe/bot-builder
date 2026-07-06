from __future__ import annotations

import logging
import uuid
from typing import Any

from app.config import settings
from app.domain.evaluation.dataset_loader import (
    builtin_dataset_id,
    load_builtin_dataset,
)
from app.domain.evaluation.metric_breakdown import build_metric_breakdown
from app.domain.evaluation.ragas_runner import (
    RagasRunner,
    answer_from_turn_evidence,
    contexts_from_turn_evidence,
)
from app.domain.graph.turn_evidence import TurnEvidence
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.infrastructure.ai.llm import BedrockLLM
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.eval_dataset_repository import EvalDatasetRepository
from app.infrastructure.db.repositories.mongo.eval_run_repository import EvalRunRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.schemas.chat import ChatRequest
from app.schemas.evaluation import (
    EvalDatasetCase,
    EvalDatasetCreate,
    EvalDatasetListItem,
    EvalDatasetListResponse,
    EvalDatasetResponse,
    EvalDummyDatasetResponse,
    EvalMode,
    EvalRunDetailResponse,
    EvalRunListResponse,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunStatus,
    EvalRunSummary,
    EvalScores,
    EvalThresholds,
)
from app.services.chat_completion_service import ChatCompletionService
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.evaluation import EvaluationDisabledError, EvalRunNotFoundError

logger = logging.getLogger(__name__)

RAG_ONLY_ANSWER_PROMPT = (
    "Answer the user question using only the retrieved context below. "
    "If the context is insufficient, say you do not have enough information.\n\n"
    "Context:\n{context}\n\nQuestion: {question}"
)


class RagEvaluationService:
    def __init__(
        self,
        *,
        agent_repository: AgentRepository,
        eval_run_repository: EvalRunRepository,
        eval_dataset_repository: EvalDatasetRepository,
        chat_completion_service: ChatCompletionService,
        runtime_bundle_loader: RuntimeBundleLoader,
        tracker_repository: TrackerRepository,
        rag_retriever: RAGRetriever | None = None,
        ragas_runner: RagasRunner | None = None,
    ) -> None:
        self._agent_repository = agent_repository
        self._eval_run_repository = eval_run_repository
        self._eval_dataset_repository = eval_dataset_repository
        self._chat_completion_service = chat_completion_service
        self._runtime_bundle_loader = runtime_bundle_loader
        self._tracker_repository = tracker_repository
        self._rag_retriever = rag_retriever or RAGRetriever()
        self._ragas_runner = ragas_runner or RagasRunner()

    def _ensure_enabled(self) -> None:
        if not settings.rag_eval_enabled:
            raise EvaluationDisabledError("RAG evaluation is disabled")

    def _thresholds(self) -> EvalThresholds:
        return EvalThresholds(
            faithfulness=settings.rag_eval_faithfulness_threshold,
            context_precision=settings.rag_eval_context_precision_threshold,
        )

    @staticmethod
    def _passed(scores: EvalScores, thresholds: EvalThresholds) -> bool:
        if scores.faithfulness is not None and scores.faithfulness < thresholds.faithfulness:
            return False
        if scores.context_precision is not None and scores.context_precision < thresholds.context_precision:
            return False
        return True

    async def run_single(
        self,
        *,
        agent_id: str,
        organization_id: str,
        request: EvalRunRequest,
    ) -> EvalRunResponse:
        self._ensure_enabled()
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")

        sender_id = request.sender_id or f"eval-{uuid.uuid4().hex[:12]}"
        turn_evidence = await self._collect_turn_evidence(
            agent_doc=agent_doc,
            agent_id=agent_id,
            organization_id=organization_id,
            request=request,
            sender_id=sender_id,
        )

        ragas_result = await self._ragas_runner.run(
            question=request.question,
            answer=answer_from_turn_evidence(turn_evidence),
            contexts=contexts_from_turn_evidence(turn_evidence),
            ground_truth=request.ground_truth,
        )
        scores = EvalScores(**ragas_result.scores)
        thresholds = self._thresholds()
        breakdown = build_metric_breakdown(
            turn_evidence=turn_evidence,
            scores=ragas_result.scores,
            ground_truth=request.ground_truth,
            faithfulness_detail=ragas_result.faithfulness_detail,
        )

        doc = await self._eval_run_repository.create(
            document={
                "organization_id": organization_id,
                "agent_id": agent_id,
                "question": request.question,
                "ground_truth": request.ground_truth,
                "mode": request.mode.value,
                "sender_id": sender_id,
                "turn_evidence": turn_evidence,
                "scores": scores.model_dump(),
                "thresholds": thresholds.model_dump(),
                "passed": self._passed(scores, thresholds),
                "status": EvalRunStatus.COMPLETE.value,
                **breakdown,
            },
        )

        return EvalRunResponse(
            run_id=str(doc["_id"]),
            status=EvalRunStatus.COMPLETE,
            scores=scores,
            thresholds=thresholds,
            passed=bool(doc["passed"]),
        )

    async def list_runs(
        self,
        *,
        agent_id: str,
        organization_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> EvalRunListResponse:
        self._ensure_enabled()
        await self._require_agent(agent_id=agent_id, organization_id=organization_id)
        items, total = await self._eval_run_repository.list_by_agent(
            agent_id=agent_id,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
        thresholds = self._thresholds()
        summaries = [
            EvalRunSummary(
                run_id=str(item["_id"]),
                question=item.get("question"),
                mode=EvalMode(item.get("mode", EvalMode.FULL_BOT.value)),
                status=EvalRunStatus(item.get("status", EvalRunStatus.COMPLETE.value)),
                scores=EvalScores(**(item.get("scores") or {})),
                thresholds=thresholds,
                passed=bool(item.get("passed", False)),
                created_at=item.get("created_at"),
            )
            for item in items
        ]
        return EvalRunListResponse(items=summaries, total=total)

    async def get_run(
        self,
        *,
        agent_id: str,
        organization_id: str,
        run_id: str,
    ) -> EvalRunDetailResponse:
        self._ensure_enabled()
        await self._require_agent(agent_id=agent_id, organization_id=organization_id)
        doc = await self._eval_run_repository.find_by_id_for_agent(
            run_id=run_id,
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if doc is None:
            raise EvalRunNotFoundError(f"Evaluation run not found: {run_id}")

        scores = EvalScores(**(doc.get("scores") or {}))
        thresholds = EvalThresholds(**(doc.get("thresholds") or self._thresholds().model_dump()))
        return EvalRunDetailResponse(
            run_id=str(doc["_id"]),
            agent_id=agent_id,
            question=str(doc.get("question", "")),
            ground_truth=doc.get("ground_truth"),
            mode=EvalMode(doc.get("mode", EvalMode.FULL_BOT.value)),
            status=EvalRunStatus(doc.get("status", EvalRunStatus.COMPLETE.value)),
            turn_evidence=dict(doc.get("turn_evidence") or {}),
            scores=scores,
            thresholds=thresholds,
            passed=bool(doc.get("passed", False)),
            faithfulness_detail=doc.get("faithfulness_detail"),
            answer_relevancy_detail=doc.get("answer_relevancy_detail"),
            context_precision_detail=doc.get("context_precision_detail"),
            context_recall_detail=doc.get("context_recall_detail"),
            created_at=doc["created_at"],
        )

    async def get_dummy_dataset(
        self,
        *,
        agent_id: str,
        organization_id: str,
    ) -> EvalDummyDatasetResponse:
        self._ensure_enabled()
        agent_doc = await self._require_agent(agent_id=agent_id, organization_id=organization_id)
        data = load_builtin_dataset(
            industry=agent_doc.get("industry"),
            agent_type=agent_doc.get("agent_type"),
        )
        return EvalDummyDatasetResponse(
            name=data["name"],
            industry=data["industry"],
            agent_type=data["agent_type"],
            cases=[EvalDatasetCase(**case) for case in data.get("cases", [])],
        )

    async def list_datasets(
        self,
        *,
        agent_id: str,
        organization_id: str,
    ) -> EvalDatasetListResponse:
        self._ensure_enabled()
        agent_doc = await self._require_agent(agent_id=agent_id, organization_id=organization_id)
        builtin = load_builtin_dataset(
            industry=agent_doc.get("industry"),
            agent_type=agent_doc.get("agent_type"),
        )
        items = [
            EvalDatasetListItem(
                dataset_id=builtin_dataset_id(
                    industry=agent_doc.get("industry"),
                    agent_type=agent_doc.get("agent_type"),
                ),
                name=str(builtin["name"]),
                source="builtin",
                case_count=len(builtin.get("cases", [])),
            ),
        ]
        custom_docs = await self._eval_dataset_repository.list_by_agent(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        for doc in custom_docs:
            cases = doc.get("cases") or []
            items.append(
                EvalDatasetListItem(
                    dataset_id=str(doc["_id"]),
                    name=str(doc.get("name", "Custom dataset")),
                    source="custom",
                    case_count=len(cases),
                ),
            )
        return EvalDatasetListResponse(items=items)

    async def create_dataset(
        self,
        *,
        agent_id: str,
        organization_id: str,
        request: EvalDatasetCreate,
    ) -> EvalDatasetResponse:
        self._ensure_enabled()
        await self._require_agent(agent_id=agent_id, organization_id=organization_id)
        doc = await self._eval_dataset_repository.create(
            document={
                "organization_id": organization_id,
                "agent_id": agent_id,
                "name": request.name,
                "cases": [case.model_dump() for case in request.cases],
                "source": "custom",
            },
        )
        return EvalDatasetResponse(
            dataset_id=str(doc["_id"]),
            name=request.name,
            case_count=len(request.cases),
        )

    async def _require_agent(self, *, agent_id: str, organization_id: str) -> dict[str, Any]:
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")
        return agent_doc

    async def _collect_turn_evidence(
        self,
        *,
        agent_doc: dict[str, Any],
        agent_id: str,
        organization_id: str,
        request: EvalRunRequest,
        sender_id: str,
    ) -> dict[str, Any]:
        if request.mode == EvalMode.FULL_BOT:
            await self._chat_completion_service.complete_preview(
                agent_id=agent_id,
                organization_id=organization_id,
                request=ChatRequest(sender_id=sender_id, message=request.question),
            )
            evidence = await self._turn_evidence_from_tracker(
                sender_id=sender_id,
                assistant_id=agent_id,
            )
            if evidence is not None:
                return evidence
            return TurnEvidence(user_message=request.question).to_dict()

        return await self._rag_only_turn_evidence(
            agent_doc=agent_doc,
            organization_id=organization_id,
            request=request,
        )

    async def _turn_evidence_from_tracker(
        self,
        *,
        sender_id: str,
        assistant_id: str,
    ) -> dict[str, Any] | None:
        doc = await self._tracker_repository.find_by_session(
            sender_id=sender_id,
            assistant_id=assistant_id,
        )
        if doc is None:
            return None
        turns = doc.get("turns") or []
        if not turns:
            return None
        evidence = turns[-1].get("turn_evidence")
        return dict(evidence) if isinstance(evidence, dict) else None

    async def _rag_only_turn_evidence(
        self,
        *,
        agent_doc: dict[str, Any],
        organization_id: str,
        request: EvalRunRequest,
    ) -> dict[str, Any]:
        bundle = await self._runtime_bundle_loader.load(agent_doc=agent_doc, for_preview=True)
        knowledge_bases = _filter_knowledge_bases(
            bundle.orchestrator.knowledge_bases,
            names=request.knowledge_base_names,
        )
        rag_result = await self._rag_retriever.retrieve(
            query=request.question,
            knowledge_bases=knowledge_bases,
            organization_id=organization_id,
        )
        evidence = TurnEvidence(user_message=request.question)
        evidence.record_rag_retrieval(query=request.question, chunks=rag_result.chunks)

        answer = ""
        if rag_result.context.strip():
            llm = BedrockLLM(temperature=0.0, max_output_tokens=512)
            answer = await llm.chat(
                system_prompt="You are a helpful assistant.",
                user_message=RAG_ONLY_ANSWER_PROMPT.format(
                    context=rag_result.context,
                    question=request.question,
                ),
                history=[],
            )
        evidence.set_assistant_replies([answer] if answer else [])
        return evidence.to_dict()


def _filter_knowledge_bases(
    knowledge_bases: list[RuntimeKnowledgeBase],
    *,
    names: list[str] | None,
) -> list[RuntimeKnowledgeBase]:
    if not names:
        return list(knowledge_bases)
    wanted = {name.strip().lower() for name in names if name.strip()}
    return [kb for kb in knowledge_bases if kb.name.strip().lower() in wanted]
