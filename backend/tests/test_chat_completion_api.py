from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.di.chat import get_chat_completion_service
from app.domain.constants.chat_constants import ASSISTANT_UNAVAILABLE_MESSAGE
from app.main import app
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_completion_service import ChatCompletionService

WEBHOOK_ID = "wh_test_chat"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    mock_service = AsyncMock(spec=ChatCompletionService)
    app.dependency_overrides[get_chat_completion_service] = lambda: mock_service
    return mock_service


def test_chat_webhook_returns_friendly_fallback_when_channel_missing(
    client: TestClient,
    mock_chat_service: AsyncMock,
) -> None:
    mock_chat_service.complete.return_value = ChatResponse(
        messages=[
            ChatMessage(
                recipient_id="user-1",
                text=ASSISTANT_UNAVAILABLE_MESSAGE,
            ),
        ],
    )

    response = client.post(
        f"/api/v1/chat/webhook/{WEBHOOK_ID}",
        json={"sender_id": "user-1", "message": "Hello"},
    )

    assert response.status_code == 200
    assert response.json()["messages"][0]["text"] == ASSISTANT_UNAVAILABLE_MESSAGE
    mock_chat_service.complete.assert_awaited_once()


def test_chat_webhook_validates_request_body(
    client: TestClient,
    mock_chat_service: AsyncMock,
) -> None:
    response = client.post(
        f"/api/v1/chat/webhook/{WEBHOOK_ID}",
        json={"sender_id": "user-1", "message": ""},
    )
    assert response.status_code == 422
    mock_chat_service.complete.assert_not_called()
