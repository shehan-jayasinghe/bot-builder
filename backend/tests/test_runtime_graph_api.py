from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.preview import get_runtime_graph_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.preview import (
    RuntimeGraphEdgeKind,
    RuntimeGraphNodeType,
    RuntimeGraphOrchestrator,
    RuntimeGraphResponse,
)
from app.services.runtime_graph_service import RuntimeGraphService
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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_get_runtime_graph_returns_graph(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RuntimeGraphService)
    mock_service.get_runtime_graph.return_value = RuntimeGraphResponse(
        agent_id=AGENT_ID,
        organization_id=ORG_ID,
        orchestrator=RuntimeGraphOrchestrator(id=AGENT_ID, name="Support Bot"),
        nodes=[
            {
                "id": AGENT_ID,
                "type": RuntimeGraphNodeType.ORCHESTRATOR,
                "label": "Support Bot",
                "description": None,
            },
            {
                "id": TOOL_ID,
                "type": RuntimeGraphNodeType.TOOL,
                "label": "transactions_analysis",
                "description": "Lookup transactions",
            },
        ],
        edges=[
            {
                "id": f"e-tool-{TOOL_ID}",
                "source": AGENT_ID,
                "target": TOOL_ID,
                "kind": RuntimeGraphEdgeKind.TOOL,
            },
        ],
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_runtime_graph_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/runtime-graph")

    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] == AGENT_ID
    assert body["orchestrator"]["name"] == "Support Bot"
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1
    mock_service.get_runtime_graph.assert_awaited_once()


def test_get_runtime_graph_agent_not_found(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RuntimeGraphService)
    mock_service.get_runtime_graph.side_effect = AgentNotFoundError("Agent not found")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_runtime_graph_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/runtime-graph")

    assert response.status_code == 404


def test_get_runtime_graph_invalid_agent_id(client: TestClient) -> None:
    mock_service = AsyncMock(spec=RuntimeGraphService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_runtime_graph_service] = lambda: mock_service

    response = client.get("/api/v1/agents/not-an-object-id/runtime-graph")

    assert response.status_code == 422
    mock_service.get_runtime_graph.assert_not_called()


def test_get_capability_catalog_preview_returns_text(client: TestClient) -> None:
    from app.schemas.preview import CapabilityCatalogPreviewResponse

    mock_service = AsyncMock(spec=RuntimeGraphService)
    mock_service.get_capability_catalog_preview.return_value = CapabilityCatalogPreviewResponse(
        agent_id=AGENT_ID,
        text="## Capability catalog\n\n### Tools\n- get_balance: Use when user asks about balance",
        has_capabilities=True,
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_runtime_graph_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/capability-catalog-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["has_capabilities"] is True
    assert "get_balance" in body["text"]
    mock_service.get_capability_catalog_preview.assert_awaited_once()
