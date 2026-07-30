from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.sub_agents import get_sub_agent_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.sub_agent import (
    ListSubAgentsResponse,
    ParameterType,
    SubAgentListItem,
    SubAgentParameter,
    SubAgentResponse,
)
from app.services.sub_agent_service import SubAgentService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.sub_agent import (
    SubAgentLimitReachedError,
    SubAgentNameExistsError,
    SubAgentNotFoundError,
)


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
SUB_AGENT_ID = "6a3f9012d8139334274fbc00"
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


def _sub_agent_response() -> SubAgentResponse:
    return SubAgentResponse(
        id=SUB_AGENT_ID,
        name="research_agent",
        description="Research specialist",
        instructions="You are a research assistant focused on factual answers.",
        tool_ids=[],
        knowledge_base_ids=[],
        workflow_ids=[],
        parameters=[
            SubAgentParameter(
                name="query",
                type=ParameterType.STRING,
                description="Research question",
            )
        ],
        status="active",
        agent_id=AGENT_ID,
        organization_id=ORG_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _sub_agent_list_item() -> SubAgentListItem:
    return SubAgentListItem(
        id=SUB_AGENT_ID,
        name="research_agent",
        description="Research specialist",
        status="active",
        tool_count=0,
        knowledge_base_count=0,
        workflow_count=0,
        parameter_count=1,
        agent_id=AGENT_ID,
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


def test_create_sub_agent_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.create = AsyncMock(return_value=_sub_agent_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/sub-agents",
        json={
            "name": "research_agent",
            "description": "Research specialist",
            "instructions": "You are a research assistant focused on factual answers.",
            "tool_ids": [],
            "knowledge_base_ids": [],
            "workflow_ids": [],
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": "Research question",
                    "required": True,
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "research_agent"
    mock_service.create.assert_awaited_once()


def test_list_sub_agents_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.list_by_agent = AsyncMock(
        return_value=ListSubAgentsResponse(items=[_sub_agent_list_item()], total=1),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/sub-agents")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    mock_service.list_by_agent.assert_awaited_once()


def test_get_sub_agent_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.get_by_id = AsyncMock(return_value=_sub_agent_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/sub-agents/{SUB_AGENT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == SUB_AGENT_ID
    mock_service.get_by_id.assert_awaited_once()


def test_update_sub_agent_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.update = AsyncMock(return_value=_sub_agent_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/agents/{AGENT_ID}/sub-agents/{SUB_AGENT_ID}",
        json={"instructions": "You are a research assistant focused on factual answers."},
    )

    assert response.status_code == 200
    mock_service.update.assert_awaited_once()


def test_get_sub_agent_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.get_by_id = AsyncMock(side_effect=SubAgentNotFoundError("Sub-agent not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/sub-agents/{SUB_AGENT_ID}")

    assert response.status_code == 404


def test_create_sub_agent_agent_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.create = AsyncMock(side_effect=AgentNotFoundError("Agent not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/sub-agents",
        json={
            "name": "research_agent",
            "instructions": "You are a research assistant focused on factual answers.",
        },
    )

    assert response.status_code == 404


def test_create_sub_agent_duplicate_name(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.create = AsyncMock(
        side_effect=SubAgentNameExistsError("Sub-agent name already exists for this agent"),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/sub-agents",
        json={
            "name": "research_agent",
            "instructions": "You are a research assistant focused on factual answers.",
        },
    )

    assert response.status_code == 409


def test_create_sub_agent_limit_reached(client: TestClient) -> None:
    mock_service = MagicMock(spec=SubAgentService)
    mock_service.create = AsyncMock(
        side_effect=SubAgentLimitReachedError("Sub-agent limit reached (10)"),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_sub_agent_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/sub-agents",
        json={
            "name": "research_agent",
            "instructions": "You are a research assistant focused on factual answers.",
        },
    )

    assert response.status_code == 409
