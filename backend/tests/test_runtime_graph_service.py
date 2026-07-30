import asyncio
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.domain.models.current_user import CurrentUser
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeKnowledgeBase,
    RuntimeOrchestrator,
    RuntimeSubAgent,
    RuntimeTool,
    RuntimeWorkflow,
)
from app.schemas.preview import RuntimeGraphNodeType
from app.services.runtime_graph_service import RuntimeGraphService, _bundle_to_graph_response
from app.shared.exceptions.agent import AgentNotFoundError

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
TOOL_ID = "6a3f9012d8139334274fbc01"


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="6a3b7c61d8139334274fbbfd",
        organization_id=ORG_ID,
        clerk_id="user_test",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        user_type="root",
        is_root=True,
        status="active",
        organization_name="abc bank",
        organization_industry="financial_services",
    )


def test_bundle_to_graph_response_maps_nodes_and_edges() -> None:
    bundle = RuntimeBundle(
        orchestrator=RuntimeOrchestrator(
            id=AGENT_ID,
            name="Support Bot",
            system_prompt="Help.",
            tools=[
                RuntimeTool(
                    id=TOOL_ID,
                    name="transactions_analysis",
                    description="Lookup transactions",
                    executor="mongo_find_many",
                    connector_id="6a3f9012d8139334274fbc05",
                    status="active",
                ),
            ],
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id="6a3f9012d8139334274fbc02",
                    name="Policy docs",
                    storage_type="vector",
                    status="ready",
                ),
            ],
            workflows=[
                RuntimeWorkflow(
                    id="6a3f9012d8139334274fbc03",
                    name="dispute_process",
                    status="published",
                ),
            ],
            sub_agents=[
                RuntimeSubAgent(
                    id="6a3f9012d8139334274fbc04",
                    name="research_agent",
                    instructions="Research.",
                    status="active",
                ),
            ],
        ),
        organization_id=ORG_ID,
    )

    response = _bundle_to_graph_response(bundle)

    assert response.agent_id == AGENT_ID
    assert response.organization_id == ORG_ID
    assert response.orchestrator.name == "Support Bot"
    assert len(response.nodes) == 5
    assert len(response.edges) == 4
    assert response.nodes[0].type == RuntimeGraphNodeType.ORCHESTRATOR
    assert any(node.label == "transactions_analysis" for node in response.nodes)
    assert all(edge.source == AGENT_ID for edge in response.edges)


def test_get_runtime_graph_raises_when_agent_missing() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = None

        service = RuntimeGraphService(
            agent_repository=agent_repository,
            runtime_bundle_loader=runtime_bundle_loader,
        )

        with pytest.raises(AgentNotFoundError):
            await service.get_runtime_graph(
                current_user=_current_user(),
                agent_id=AGENT_ID,
            )

    asyncio.run(_run())


def test_get_runtime_graph_loads_bundle() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = {
            "_id": ObjectId(AGENT_ID),
            "organization_id": ORG_ID,
            "name": "Support Bot",
            "system_prompt": "Help.",
        }
        runtime_bundle_loader.load.return_value = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=AGENT_ID,
                name="Support Bot",
                system_prompt="Help.",
            ),
            organization_id=ORG_ID,
        )

        service = RuntimeGraphService(
            agent_repository=agent_repository,
            runtime_bundle_loader=runtime_bundle_loader,
        )

        response = await service.get_runtime_graph(
            current_user=_current_user(),
            agent_id=AGENT_ID,
        )

        assert response.orchestrator.id == AGENT_ID
        runtime_bundle_loader.load.assert_awaited_once_with(
            agent_doc=agent_repository.find_by_id_for_organization.return_value,
            for_preview=True,
        )

    asyncio.run(_run())
