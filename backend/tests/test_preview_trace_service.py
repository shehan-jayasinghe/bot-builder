import asyncio
from unittest.mock import AsyncMock

import pytest

from app.domain.models.current_user import CurrentUser
from app.schemas.preview import PreviewTraceEvent, PreviewTraceTurn
from app.services.preview_trace_service import PreviewTraceService, _map_turns
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


def test_map_turns_parses_events() -> None:
    turns = _map_turns(
        [
            {
                "turn_id": "turn-1",
                "started_at": "2026-06-20T21:33:35.100Z",
                "events": [
                    {
                        "type": "input_message",
                        "at": "2026-06-20T21:33:35.100Z",
                        "data": {"message": "Hi"},
                    },
                ],
                "routing_decision": {"mode": "orchestrator"},
                "turn_evidence": {
                    "user_message": "Hi",
                    "assistant_replies": ["Hello"],
                    "rag_retrievals": [],
                    "tool_calls": [],
                    "routing": {"mode": "orchestrator"},
                },
            },
        ],
    )

    assert len(turns) == 1
    assert turns[0].events[0].type == "input_message"
    assert turns[0].routing_decision == {"mode": "orchestrator"}
    assert turns[0].turn_evidence is not None
    assert turns[0].turn_evidence["user_message"] == "Hi"


def test_get_session_trace_returns_empty_when_no_session() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_repository = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = {"_id": AGENT_ID}
        tracker_repository.find_by_session.return_value = None

        service = PreviewTraceService(
            agent_repository=agent_repository,
            tracker_repository=tracker_repository,
        )

        response = await service.get_session_trace(
            current_user=_current_user(),
            agent_id=AGENT_ID,
            sender_id=SENDER_ID,
        )

        assert response.turns == []
        assert response.sender_id == SENDER_ID

    asyncio.run(_run())


def test_get_session_trace_returns_turns() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_repository = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = {"_id": AGENT_ID}
        tracker_repository.find_by_session.return_value = {
            "sender_id": SENDER_ID,
            "assistant_id": AGENT_ID,
            "organization_id": ORG_ID,
            "source": "preview",
            "turns": [
                {
                    "turn_id": "turn-1",
                    "started_at": "2026-06-20T21:33:35.100Z",
                    "events": [
                        {
                            "type": "output_message",
                            "at": "2026-06-20T21:33:37.000Z",
                            "data": {"text": "Hello"},
                        },
                    ],
                    "routing_decision": {"mode": "orchestrator"},
                },
            ],
        }

        service = PreviewTraceService(
            agent_repository=agent_repository,
            tracker_repository=tracker_repository,
        )

        response = await service.get_session_trace(
            current_user=_current_user(),
            agent_id=AGENT_ID,
            sender_id=SENDER_ID,
        )

        assert response.source == "preview"
        assert len(response.turns) == 1
        assert response.turns[0].events[0].type == "output_message"

    asyncio.run(_run())


def test_get_session_trace_raises_when_agent_missing() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        agent_repository.find_by_id_for_organization.return_value = None

        service = PreviewTraceService(
            agent_repository=agent_repository,
            tracker_repository=AsyncMock(),
        )

        with pytest.raises(AgentNotFoundError):
            await service.get_session_trace(
                current_user=_current_user(),
                agent_id=AGENT_ID,
                sender_id=SENDER_ID,
            )

    asyncio.run(_run())
