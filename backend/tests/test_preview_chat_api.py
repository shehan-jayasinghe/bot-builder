from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.chat import get_chat_completion_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_completion_service import ChatCompletionService
from app.shared.exceptions.agent import AgentNotFoundError

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"


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


def test_preview_chat_returns_reply(client: TestClient) -> None:
    mock_service = AsyncMock(spec=ChatCompletionService)
    mock_service.complete_preview.return_value = ChatResponse(
        messages=[
            ChatMessage(
                recipient_id="preview-session-1",
                text="Hello from preview",
            ),
        ],
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_chat_completion_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/preview/chat",
        json={"sender_id": "preview-session-1", "message": "Hi"},
    )

    assert response.status_code == 200
    assert response.json()["messages"][0]["text"] == "Hello from preview"
    mock_service.complete_preview.assert_awaited_once()


def test_preview_chat_agent_not_found(client: TestClient) -> None:
    mock_service = AsyncMock(spec=ChatCompletionService)
    mock_service.complete_preview.side_effect = AgentNotFoundError("Agent not found")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_chat_completion_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/preview/chat",
        json={"sender_id": "preview-session-1", "message": "Hi"},
    )

    assert response.status_code == 404


def test_preview_chat_validates_body(client: TestClient) -> None:
    mock_service = AsyncMock(spec=ChatCompletionService)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_chat_completion_service] = lambda: mock_service

    response = client.post(
        f"/api/v1/agents/{AGENT_ID}/preview/chat",
        json={"sender_id": "preview-session-1", "message": ""},
    )

    assert response.status_code == 422
    mock_service.complete_preview.assert_not_called()
