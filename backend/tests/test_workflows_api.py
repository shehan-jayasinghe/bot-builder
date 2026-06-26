from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.domain.models.current_user import CurrentUser
from app.main import app
from app.di.auth import get_current_user
from app.di.workflows import get_workflow_service
from app.schemas.workflow import CreateWorkflowRequest, ListWorkflowsResponse, WorkflowListItem, WorkflowResponse
from app.services.workflow_service import WorkflowService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.workflow import WorkflowLimitReachedError, WorkflowNotFoundError


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
WORKFLOW_ID = "6a3f9012d8139334274fbc00"
NOW = datetime(2026, 6, 26, 10, 0, 0, tzinfo=UTC)


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


def _workflow_response() -> WorkflowResponse:
    return WorkflowResponse(
        id=WORKFLOW_ID,
        name="Welcome",
        description=None,
        agent_id=None,
        status="draft",
        nodes=[
            {
                "id": "start-1",
                "type": "start",
                "position": {"x": 120, "y": 220},
                "data": {},
            },
            {
                "id": "message-1",
                "type": "message",
                "position": {"x": 320, "y": 220},
                "data": {"text": "Welcome"},
            },
        ],
        edges=[{"id": "edge-1", "source": "start-1", "target": "message-1"}],
        organization_id=ORG_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _workflow_list_item() -> WorkflowListItem:
    return WorkflowListItem(
        id=WORKFLOW_ID,
        name="Welcome",
        description=None,
        agent_id=None,
        status="draft",
        node_count=2,
        organization_id=ORG_ID,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_create_workflow_endpoint_minimal_body(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.create = AsyncMock(return_value=_workflow_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.post("/api/v1/workflows", json={})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Welcome"
    assert body["status"] == "draft"
    assert len(body["nodes"]) == 2
    mock_service.create.assert_awaited_once()


def test_create_workflow_endpoint_with_agent(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    response_payload = _workflow_response().model_copy(update={"agent_id": AGENT_ID})
    mock_service.create = AsyncMock(return_value=response_payload)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.post(
        "/api/v1/workflows",
        json={"name": "Onboarding", "agent_id": AGENT_ID},
    )

    assert response.status_code == 201
    assert response.json()["agent_id"] == AGENT_ID


def test_create_workflow_endpoint_agent_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.create = AsyncMock(side_effect=AgentNotFoundError("Agent not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.post(
        "/api/v1/workflows",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 404


def test_create_workflow_endpoint_limit_reached(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.create = AsyncMock(
        side_effect=WorkflowLimitReachedError("Organization workflow limit reached (5)")
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.post("/api/v1/workflows", json={})

    assert response.status_code == 409


def test_create_workflow_endpoint_invalid_agent_id(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.post(
        "/api/v1/workflows",
        json={"agent_id": "not-an-object-id"},
    )

    assert response.status_code == 422
    mock_service.create.assert_not_called()


def test_list_workflows_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListWorkflowsResponse(items=[_workflow_list_item()], total=1)
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.get("/api/v1/workflows")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Welcome"
    assert body["items"][0]["node_count"] == 2
    assert "nodes" not in body["items"][0]
    mock_service.list_by_organization.assert_awaited_once()


def test_list_workflows_endpoint_with_filters(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListWorkflowsResponse(items=[], total=0)
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.get(
        f"/api/v1/workflows?status=draft&agent_id={AGENT_ID}",
    )

    assert response.status_code == 200
    mock_service.list_by_organization.assert_awaited_once_with(
        current_user=_current_user(),
        status="draft",
        agent_id=AGENT_ID,
    )


def test_get_workflow_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.get_by_id = AsyncMock(return_value=_workflow_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.get(f"/api/v1/workflows/{WORKFLOW_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == WORKFLOW_ID
    assert body["name"] == "Welcome"
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1
    mock_service.get_by_id.assert_awaited_once()


def test_get_workflow_endpoint_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.get_by_id = AsyncMock(side_effect=WorkflowNotFoundError("Workflow not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.get(f"/api/v1/workflows/{WORKFLOW_ID}")

    assert response.status_code == 404


def test_get_workflow_endpoint_invalid_id(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.get("/api/v1/workflows/not-an-object-id")

    assert response.status_code == 422
    mock_service.get_by_id.assert_not_called()


def test_update_workflow_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    updated = _workflow_response().model_copy(update={"name": "Customer onboarding"})
    mock_service.update = AsyncMock(return_value=updated)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/workflows/{WORKFLOW_ID}",
        json={"name": "Customer onboarding"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Customer onboarding"
    mock_service.update.assert_awaited_once()


def test_update_workflow_endpoint_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.update = AsyncMock(side_effect=WorkflowNotFoundError("Workflow not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/workflows/{WORKFLOW_ID}",
        json={"name": "Renamed"},
    )

    assert response.status_code == 404


def test_update_workflow_endpoint_empty_body(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.patch(f"/api/v1/workflows/{WORKFLOW_ID}", json={})

    assert response.status_code == 422
    mock_service.update.assert_not_called()


def test_update_workflow_endpoint_agent_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=WorkflowService)
    mock_service.update = AsyncMock(side_effect=AgentNotFoundError("Agent not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_workflow_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/workflows/{WORKFLOW_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 404
