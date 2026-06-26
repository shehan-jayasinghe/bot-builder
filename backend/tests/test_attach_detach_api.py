from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.knowledgebases import get_knowledgebase_service
from app.di.tools import get_tool_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.knowledgebase import (
    KnowledgebaseListItem,
    ListKnowledgebasesResponse,
    SourceType,
    StorageType,
    UpdateKnowledgebaseResponse,
)
from app.schemas.tool import ExecutorName, ListToolsResponse, ToolListItem, ToolResponse
from app.services.knowledgebase_service import KnowledgebaseService
from app.services.tool_service import ToolService
from app.shared.exceptions.agent import AgentNotFoundError
from app.shared.exceptions.knowledgebase import KnowledgebaseNotFoundError
from app.shared.exceptions.tool import ToolNameExistsError, ToolNotFoundError


ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
OTHER_AGENT_ID = "6a3b7c61d8139334274fbbf2"
KB_ID = "6a3f9012d8139334274fbc01"
TOOL_ID = "6a3f9012d8139334274fbc00"
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


def _kb_list_item() -> KnowledgebaseListItem:
    return KnowledgebaseListItem(
        id=KB_ID,
        name="Policy docs",
        description=None,
        source_type=SourceType.FILE,
        storage_type=StorageType.VECTOR,
        website_url=None,
        crawl_depth=None,
        agent_id=AGENT_ID,
        status="ready",
        organization_id=ORG_ID,
        created_at=NOW,
    )


def _kb_update_response() -> UpdateKnowledgebaseResponse:
    return UpdateKnowledgebaseResponse(
        id=KB_ID,
        name="Policy docs",
        description=None,
        source_type=SourceType.FILE,
        storage_type=StorageType.VECTOR,
        website_url=None,
        crawl_depth=None,
        agent_id=AGENT_ID,
        status="ready",
        organization_id=ORG_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _tool_list_item() -> ToolListItem:
    return ToolListItem(
        id=TOOL_ID,
        name="customer_lookup",
        description="Lookup customer",
        executor=ExecutorName.MONGO_FIND_ONE,
        connector_id="6a3f8c12d8139334274fbbfe",
        config={"collection": "customers"},
        status="active",
        agent_id=AGENT_ID,
        organization_id=ORG_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _tool_response() -> ToolResponse:
    return ToolResponse(**_tool_list_item().model_dump())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_list_knowledgebases_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListKnowledgebasesResponse(items=[_kb_list_item()], total=1),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.get("/api/v1/knowledgebases")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    mock_service.list_by_organization.assert_awaited_once()


def test_list_knowledgebases_endpoint_with_agent_filter(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListKnowledgebasesResponse(items=[], total=0),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.get(f"/api/v1/knowledgebases?agent_id={AGENT_ID}")

    assert response.status_code == 200
    mock_service.list_by_organization.assert_awaited_once()


def test_update_knowledgebase_attach_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    mock_service.update = AsyncMock(return_value=_kb_update_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/knowledgebases/{KB_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 200
    assert response.json()["agent_id"] == AGENT_ID


def test_update_knowledgebase_detach_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    mock_service.update = AsyncMock(
        return_value=_kb_update_response().model_copy(update={"agent_id": None}),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/knowledgebases/{KB_ID}",
        json={"agent_id": None},
    )

    assert response.status_code == 200
    assert response.json()["agent_id"] is None


def test_update_knowledgebase_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    mock_service.update = AsyncMock(side_effect=KnowledgebaseNotFoundError("Knowledge base not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/knowledgebases/{KB_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 404


def test_update_knowledgebase_empty_body(client: TestClient) -> None:
    mock_service = MagicMock(spec=KnowledgebaseService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_knowledgebase_service] = lambda: mock_service

    response = client.patch(f"/api/v1/knowledgebases/{KB_ID}", json={})

    assert response.status_code == 422


def test_list_tools_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListToolsResponse(items=[_tool_list_item()], total=1),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.get("/api/v1/tools")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_tools_endpoint_with_agent_filter(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.list_by_organization = AsyncMock(
        return_value=ListToolsResponse(items=[], total=0),
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.get(f"/api/v1/tools?agent_id={AGENT_ID}")

    assert response.status_code == 200


def test_update_tool_attach_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.update = AsyncMock(return_value=_tool_response())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/tools/{TOOL_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 200
    assert response.json()["agent_id"] == AGENT_ID


def test_update_tool_detach_endpoint(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.update = AsyncMock(return_value=_tool_response().model_copy(update={"agent_id": None}))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/tools/{TOOL_ID}",
        json={"agent_id": None},
    )

    assert response.status_code == 200
    assert response.json()["agent_id"] is None


def test_update_tool_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.update = AsyncMock(side_effect=ToolNotFoundError("Tool not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/tools/{TOOL_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 404


def test_update_tool_name_conflict(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.update = AsyncMock(side_effect=ToolNameExistsError("Tool name already exists for this agent"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/tools/{TOOL_ID}",
        json={"agent_id": OTHER_AGENT_ID},
    )

    assert response.status_code == 409


def test_update_tool_agent_not_found(client: TestClient) -> None:
    mock_service = MagicMock(spec=ToolService)
    mock_service.update = AsyncMock(side_effect=AgentNotFoundError("Agent not found"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_tool_service] = lambda: mock_service

    response = client.patch(
        f"/api/v1/tools/{TOOL_ID}",
        json={"agent_id": AGENT_ID},
    )

    assert response.status_code == 404
