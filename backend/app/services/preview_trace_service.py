from typing import Any

from app.domain.models.current_user import CurrentUser
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.infrastructure.db.repositories.mongo.tracker_repository import TrackerRepository
from app.schemas.preview import PreviewTraceEvent, PreviewTraceResponse, PreviewTraceTurn
from app.shared.exceptions.agent import AgentNotFoundError


class PreviewTraceService:
    def __init__(
        self,
        *,
        agent_repository: AgentRepository,
        tracker_repository: TrackerRepository,
    ) -> None:
        self._agent_repository = agent_repository
        self._tracker_repository = tracker_repository

    async def get_session_trace(
        self,
        *,
        current_user: CurrentUser,
        agent_id: str,
        sender_id: str,
    ) -> PreviewTraceResponse:
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=current_user.organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")

        doc = await self._tracker_repository.find_by_session(
            sender_id=sender_id,
            assistant_id=agent_id,
        )
        if doc is None:
            return PreviewTraceResponse(agent_id=agent_id, sender_id=sender_id, turns=[])

        if doc.get("organization_id") and doc["organization_id"] != current_user.organization_id:
            return PreviewTraceResponse(agent_id=agent_id, sender_id=sender_id, turns=[])

        return PreviewTraceResponse(
            agent_id=agent_id,
            sender_id=sender_id,
            source=_optional_str(doc.get("source")),
            turns=_map_turns(doc.get("turns")),
        )


def _map_turns(raw_turns: Any) -> list[PreviewTraceTurn]:
    if not isinstance(raw_turns, list):
        return []

    turns: list[PreviewTraceTurn] = []
    for item in raw_turns:
        if not isinstance(item, dict):
            continue
        turn_id = item.get("turn_id")
        started_at = item.get("started_at")
        if not turn_id or not started_at:
            continue
        events = [
            PreviewTraceEvent(
                type=str(event["type"]),
                at=str(event["at"]),
                data=dict(event.get("data") or {}),
            )
            for event in (item.get("events") or [])
            if isinstance(event, dict) and event.get("type") and event.get("at")
        ]
        routing = item.get("routing_decision")
        evidence = item.get("turn_evidence")
        turns.append(
            PreviewTraceTurn(
                turn_id=str(turn_id),
                started_at=str(started_at),
                events=events,
                routing_decision=dict(routing) if isinstance(routing, dict) else None,
                turn_evidence=dict(evidence) if isinstance(evidence, dict) else None,
            ),
        )
    return turns


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
