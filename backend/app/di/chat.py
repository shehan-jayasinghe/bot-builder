from fastapi import Depends

from app.di.repositories import (
    get_connector_repository,
    get_knowledgebase_repository,
    get_sub_agent_repository,
    get_tool_repository,
    get_workflow_repository,
)
from app.di.services import get_assistant_loader, get_tracker_service
from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.pipeline.guardrails.runner import GuardrailRunner
from app.domain.pipeline.observability.trace import TraceCollector
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.infrastructure.db.repositories.mongo.knowledgebase_repository import KnowledgebaseRepository
from app.infrastructure.db.repositories.mongo.sub_agent_repository import SubAgentRepository
from app.infrastructure.db.repositories.mongo.tool_repository import ToolRepository
from app.infrastructure.db.repositories.mongo.workflow_repository import WorkflowRepository
from app.services.assistant_loader import AssistantLoader
from app.services.chat_completion_service import ChatCompletionService
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.services.tracker_service import TrackerService


def get_runtime_bundle_loader(
    tool_repository: ToolRepository = Depends(get_tool_repository),
    knowledgebase_repository: KnowledgebaseRepository = Depends(get_knowledgebase_repository),
    workflow_repository: WorkflowRepository = Depends(get_workflow_repository),
    sub_agent_repository: SubAgentRepository = Depends(get_sub_agent_repository),
    connector_repository: ConnectorRepository = Depends(get_connector_repository),
) -> RuntimeBundleLoader:
    return RuntimeBundleLoader(
        tool_repository=tool_repository,
        knowledgebase_repository=knowledgebase_repository,
        workflow_repository=workflow_repository,
        sub_agent_repository=sub_agent_repository,
        connector_repository=connector_repository,
    )


def get_chat_completion_service(
    assistant_loader: AssistantLoader = Depends(get_assistant_loader),
    tracker_service: TrackerService = Depends(get_tracker_service),
    runtime_bundle_loader: RuntimeBundleLoader = Depends(get_runtime_bundle_loader),
) -> ChatCompletionService:
    return ChatCompletionService(
        assistant_loader=assistant_loader,
        tracker_service=tracker_service,
        runtime_bundle_loader=runtime_bundle_loader,
        guardrails=GuardrailRunner(),
        rag=RAGRetriever(),
        orchestrator=OrchestratorRunner(),
        trace=TraceCollector(),
    )
