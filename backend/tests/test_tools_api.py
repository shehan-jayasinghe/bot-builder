import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.domain.constants.executor_constants import ExecutorName
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.di.auth import get_current_user
from app.di.tools import get_tool_service
from app.schemas.tool import CreateToolRequest, ListToolsResponse, ToolListItem, ToolResponse
from app.services.tool_service import ToolService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.tool import ToolNotFoundError


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
CONNECTOR_ID = "6a3f8c12d8139334274fbbfe"
TOOL_ID = "6a3f9012d8139334274fbc00"
NOW = datetime(2026, 6, 25, 12, 0, 0, tzinfo=UTC)


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


def _tool_response() -> ToolResponse:
    return ToolResponse(
        id=TOOL_ID,
        name="customer_lookup",
        description="Get customer loyalty info",
        executor=ExecutorName.MONGO_FIND_ONE,
        connector_id=CONNECTOR_ID,
        config={
            "collection": "customers",
            "filter": {"customer_id": "{{customer_id}}"},
        },
        status="active",
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


def test_create_tool_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.create = AsyncMock(return_value=_tool_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/tools",
        json={
            "name": "customer_lookup",
            "description": "Get customer loyalty info",
            "executor": "mongo_find_one",
            "connector_id": CONNECTOR_ID,
            "config": {
                "collection": "customers",
                "filter": {"customer_id": "{{customer_id}}"},
            },
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "customer_lookup"
    assert body["executor"] == "mongo_find_one"
    mock_service.create.assert_awaited_once()


def test_list_tools_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.list_by_agent = AsyncMock(
        return_value=ListToolsResponse(items=[ToolListItem(**_tool_response().model_dump())], total=1)
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/tools")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "customer_lookup"
    mock_service.list_by_agent.assert_awaited_once()


def test_get_tool_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.get_by_id = AsyncMock(return_value=_tool_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/tools/{TOOL_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == TOOL_ID
    mock_service.get_by_id.assert_awaited_once()


def test_get_tool_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.get_by_id = AsyncMock(side_effect=ToolNotFoundError("Tool not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/tools/{TOOL_ID}")

    assert response.status_code == 404


def test_tool_service_create() -> None:
    async def _run() -> None:
        tool_repo = MagicMock()
        agent_repo = MagicMock()
        connector_repo = MagicMock()

        tool_repo.find_by_name_for_agent = AsyncMock(return_value=None)
        tool_repo.create = AsyncMock(
            return_value={
                "_id": ObjectId(TOOL_ID),
                "name": "customer_lookup",
                "description": "Get customer loyalty info",
                "executor": "mongo_find_one",
                "connector_id": CONNECTOR_ID,
                "config": {"collection": "customers", "filter": {"customer_id": "{{customer_id}}"}},
                "status": "active",
                "organization_id": ORG_ID,
                "agent_id": AGENT_ID,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        agent_repo.find_by_id_for_organization = AsyncMock(return_value={"_id": ObjectId(AGENT_ID)})
        agent_repo.push_tool_id = AsyncMock(return_value=True)
        connector_repo.find_by_id_for_organization = AsyncMock(
            return_value={"type": "mongo", "config": {"uri": "mongodb://localhost", "database": "db"}}
        )

        service = ToolService(
            tool_repository=tool_repo,
            agent_repository=agent_repo,
            connector_repository=connector_repo,
        )
        result = await service.create(
            current_user=_current_user(),
            agent_id=AGENT_ID,
            request=CreateToolRequest(
                name="customer_lookup",
                description="Get customer loyalty info",
                executor=ExecutorName.MONGO_FIND_ONE,
                connector_id=CONNECTOR_ID,
                config={
                    "collection": "customers",
                    "filter": {"customer_id": "{{customer_id}}"},
                },
            ),
        )
        assert result.name == "customer_lookup"
        agent_repo.push_tool_id.assert_awaited_once()

    asyncio.run(_run())


def test_tool_service_get_agent_not_found() -> None:
    async def _run() -> None:
        agent_repo = MagicMock()
        agent_repo.find_by_id_for_organization = AsyncMock(return_value=None)
        service = ToolService(
            tool_repository=MagicMock(),
            agent_repository=agent_repo,
            connector_repository=MagicMock(),
        )
        with pytest.raises(AgentNotFoundError):
            await service.list_by_agent(
                current_user=_current_user(),
                agent_id=AGENT_ID,
            )

    asyncio.run(_run())
