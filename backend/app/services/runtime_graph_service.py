from app.domain.models.current_user import CurrentUser
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeWorkflow
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.domain.pipeline.prompt.capability_catalog_builder import CapabilityCatalogBuilder
from app.schemas.preview import (
    CapabilityCatalogPreviewResponse,
    RuntimeGraphEdge,
    RuntimeGraphEdgeKind,
    RuntimeGraphNode,
    RuntimeGraphNodeType,
    RuntimeGraphOrchestrator,
    RuntimeGraphResponse,
)
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.shared.exceptions.agent import AgentNotFoundError


class RuntimeGraphService:
    def __init__(
        self,
        *,
        agent_repository: AgentRepository,
        runtime_bundle_loader: RuntimeBundleLoader,
    ) -> None:
        self._agent_repository = agent_repository
        self._runtime_bundle_loader = runtime_bundle_loader

    async def get_runtime_graph(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
    ) -> RuntimeGraphResponse:
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")

        bundle = await self._runtime_bundle_loader.load(agent_doc=agent_doc, for_preview=True)
        return _bundle_to_graph_response(bundle, agent_doc=agent_doc)

    async def get_capability_catalog_preview(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
    ) -> CapabilityCatalogPreviewResponse:
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")

        bundle = await self._runtime_bundle_loader.load(agent_doc=agent_doc, for_preview=True)
        text = CapabilityCatalogBuilder().build(bundle=bundle)
        return CapabilityCatalogPreviewResponse(
            agent_id=agent_id,
            text=text,
            has_capabilities=bool(text),
        )


def _bundle_to_graph_response(
    bundle: RuntimeBundle,
    *,
    agent_doc: dict | None = None,
) -> RuntimeGraphResponse:
    orchestrator = bundle.orchestrator
    agent_id = orchestrator.id
    agent_status = str(agent_doc.get("status")) if agent_doc and agent_doc.get("status") else None
    agent_description = str(agent_doc["description"]) if agent_doc and agent_doc.get("description") else None

    nodes: list[RuntimeGraphNode] = [
        RuntimeGraphNode(
            id=agent_id,
            type=RuntimeGraphNodeType.ORCHESTRATOR,
            label=orchestrator.name,
            description=agent_description,
        ),
    ]
    edges: list[RuntimeGraphEdge] = []

    for tool in orchestrator.tools:
        nodes.append(
            RuntimeGraphNode(
                id=tool.id,
                type=RuntimeGraphNodeType.TOOL,
                label=tool.name,
                description=tool.description,
            ),
        )
        edges.append(
            RuntimeGraphEdge(
                id=f"e-tool-{tool.id}",
                source=agent_id,
                target=tool.id,
                kind=RuntimeGraphEdgeKind.TOOL,
            ),
        )

    for workflow in orchestrator.workflows:
        nodes.append(
            RuntimeGraphNode(
                id=workflow.id,
                type=RuntimeGraphNodeType.WORKFLOW,
                label=workflow.name,
                description=_workflow_node_description(workflow),
            ),
        )
        edges.append(
            RuntimeGraphEdge(
                id=f"e-workflow-{workflow.id}",
                source=agent_id,
                target=workflow.id,
                kind=RuntimeGraphEdgeKind.WORKFLOW,
            ),
        )

    for sub_agent in orchestrator.sub_agents:
        nodes.append(
            RuntimeGraphNode(
                id=sub_agent.id,
                type=RuntimeGraphNodeType.SUB_AGENT,
                label=sub_agent.name,
                description=sub_agent.description,
            ),
        )
        edges.append(
            RuntimeGraphEdge(
                id=f"e-sub-agent-{sub_agent.id}",
                source=agent_id,
                target=sub_agent.id,
                kind=RuntimeGraphEdgeKind.SUB_AGENT,
            ),
        )

    for kb in orchestrator.knowledge_bases:
        nodes.append(
            RuntimeGraphNode(
                id=kb.id,
                type=RuntimeGraphNodeType.KNOWLEDGE_BASE,
                label=kb.name,
                description=kb.description,
            ),
        )
        edges.append(
            RuntimeGraphEdge(
                id=f"e-kb-{kb.id}",
                source=agent_id,
                target=kb.id,
                kind=RuntimeGraphEdgeKind.KNOWLEDGE_BASE,
            ),
        )

    return RuntimeGraphResponse(
        agent_id=agent_id,
        organization_id=bundle.organization_id,
        orchestrator=RuntimeGraphOrchestrator(
            id=agent_id,
            name=orchestrator.name,
            status=agent_status,
            description=agent_description,
        ),
        nodes=nodes,
        edges=edges,
    )


def _workflow_node_description(workflow: RuntimeWorkflow) -> str | None:
    parts: list[str] = []
    if workflow.description:
        parts.append(workflow.description)
    if workflow.status:
        parts.append(f"Status: {workflow.status}")
    return " · ".join(parts) if parts else None
