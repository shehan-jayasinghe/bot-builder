from fastapi import Depends

from app.di.chat import get_chat_completion_service, get_runtime_bundle_loader
from app.di.repositories import (
    get_agent_repository,
    get_eval_dataset_repository,
    get_eval_run_repository,
    get_tracker_repository,
)
from app.domain.evaluation.ragas_runner import RagasRunner
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.eval_dataset_repository import EvalDatasetRepository
from app.infrastructure.db.repositories.mongo.eval_run_repository import EvalRunRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.services.chat_completion_service import ChatCompletionService
from app.services.rag_evaluation_service import RagEvaluationService
from app.services.runtime_bundle_loader import RuntimeBundleLoader


def get_ragas_runner() -> RagasRunner:
    return RagasRunner()


def get_rag_evaluation_service(
    agent_repository: AgentRepository = Depends(get_agent_repository),
    eval_run_repository: EvalRunRepository = Depends(get_eval_run_repository),
    eval_dataset_repository: EvalDatasetRepository = Depends(get_eval_dataset_repository),
    chat_completion_service: ChatCompletionService = Depends(get_chat_completion_service),
    runtime_bundle_loader: RuntimeBundleLoader = Depends(get_runtime_bundle_loader),
    tracker_repository: TrackerRepository = Depends(get_tracker_repository),
    ragas_runner: RagasRunner = Depends(get_ragas_runner),
) -> RagEvaluationService:
    return RagEvaluationService(
        agent_repository=agent_repository,
        eval_run_repository=eval_run_repository,
        eval_dataset_repository=eval_dataset_repository,
        chat_completion_service=chat_completion_service,
        runtime_bundle_loader=runtime_bundle_loader,
        tracker_repository=tracker_repository,
        rag_retriever=RAGRetriever(),
        ragas_runner=ragas_runner,
    )
