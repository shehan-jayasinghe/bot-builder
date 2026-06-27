from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.di.auth import get_current_user
from app.di.preview import get_preview_trace_service
from app.domain.models.current_user import CurrentUser
from app.main import app
from app.schemas.preview import PreviewTraceEvent, PreviewTraceResponse, PreviewTraceTurn
from app.services.preview_trace_service import PreviewTraceService
from app.shared.exceptions.agent import AgentNotFoundError

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = "6a3b7c61d8139334274fbbf1"
SENDER_ID = "preview-session-9f2a"


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


def test_get_preview_trace_returns_turns(client: TestClient) -> None:
    mock_service = AsyncMock(spec=PreviewTraceService)
    mock_service.get_session_trace.return_value = PreviewTraceResponse(
        agent_id=AGENT_ID,
        sender_id=SENDER_ID,
        source="preview",
        turns=[
            PreviewTraceTurn(
                turn_id="turn-1",
                started_at="2026-06-20T21:33:35.100Z",
                events=[
                    PreviewTraceEvent(
                        type="input_message",
                        at="2026-06-20T21:33:35.100Z",
                        data={"message": "Hi"},
                    ),
                ],
                routing_decision={"mode": "orchestrator"},
            ),
        ],
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_preview_trace_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/preview/sessions/{SENDER_ID}/trace")

    assert response.status_code == 200
    body = response.json()
    assert body["sender_id"] == SENDER_ID
    assert len(body["turns"]) == 1
    mock_service.get_session_trace.assert_awaited_once()


def test_get_preview_trace_agent_not_found(client: TestClient) -> None:
    mock_service = AsyncMock(spec=PreviewTraceService)
    mock_service.get_session_trace.side_effect = AgentNotFoundError("Agent not found")
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_preview_trace_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/preview/sessions/{SENDER_ID}/trace")

    assert response.status_code == 404


def test_get_preview_trace_empty_session(client: TestClient) -> None:
    mock_service = AsyncMock(spec=PreviewTraceService)
    mock_service.get_session_trace.return_value = PreviewTraceResponse(
        agent_id=AGENT_ID,
        sender_id=SENDER_ID,
        turns=[],
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_preview_trace_service] = lambda: mock_service

    response = client.get(f"/api/v1/agents/{AGENT_ID}/preview/sessions/{SENDER_ID}/trace")

    assert response.status_code == 200
    assert response.json()["turns"] == []
