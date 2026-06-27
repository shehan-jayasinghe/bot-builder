from fastapi import Depends

from app.di.chat import get_runtime_bundle_loader
from app.di.repositories import get_agent_repository
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.services.runtime_graph_service import RuntimeGraphService


def get_runtime_graph_service(
    agent_repository: AgentRepository = Depends(get_agent_repository),
    runtime_bundle_loader: RuntimeBundleLoader = Depends(get_runtime_bundle_loader),
) -> RuntimeGraphService:
    return RuntimeGraphService(
        agent_repository=agent_repository,
        runtime_bundle_loader=runtime_bundle_loader,
    )
