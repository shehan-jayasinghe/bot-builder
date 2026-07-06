from datetime import UTC, datetime
from typing import Any


class Tracker:
    """In-memory session and conversation history for one sender + assistant pair."""

    def __init__(
        self,
        sender_id: str,
        assistant_id: str,
        *,
        events: list[dict[str, Any]] | None = None,
        active_flow_state: dict[str, Any] | None = None,
        active_agent_id: str | None = None,
        active_agent_kind: str | None = None,
        last_routing_decision: dict[str, Any] | None = None,
        source: str | None = None,
        organization_id: str | None = None,
        turns: list[dict[str, Any]] | None = None,
        current_turn_events: list[dict[str, Any]] | None = None,
    ) -> None:
        self._sender_id = sender_id
        self._assistant_id = assistant_id
        self._events: list[dict[str, Any]] = list(events or [])
        self._active_flow_state = active_flow_state
        self._active_agent_id = active_agent_id or assistant_id
        self._active_agent_kind = active_agent_kind or "orchestrator"
        self._last_routing_decision = last_routing_decision
        self._source = source
        self._organization_id = organization_id
        self._turns: list[dict[str, Any]] = list(turns or [])
        self._current_turn_events: list[dict[str, Any]] = list(current_turn_events or [])

    @property
    def sender_id(self) -> str:
        return self._sender_id

    @property
    def assistant_id(self) -> str:
        return self._assistant_id

    @property
    def active_flow_state(self) -> dict[str, Any] | None:
        return self._active_flow_state

    @property
    def active_agent_id(self) -> str:
        return self._active_agent_id

    @property
    def active_agent_kind(self) -> str:
        return self._active_agent_kind

    @property
    def last_routing_decision(self) -> dict[str, Any] | None:
        return self._last_routing_decision

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def organization_id(self) -> str | None:
        return self._organization_id

    @property
    def turns(self) -> list[dict[str, Any]]:
        return list(self._turns)

    def set_source(self, source: str) -> None:
        self._source = source

    def set_organization_id(self, organization_id: str) -> None:
        self._organization_id = organization_id

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "Tracker":
        return cls(
            sender_id=data["sender_id"],
            assistant_id=data["assistant_id"],
            events=data.get("events", []),
            active_flow_state=data.get("active_flow_state"),
            active_agent_id=data.get("active_agent_id"),
            active_agent_kind=data.get("active_agent_kind"),
            last_routing_decision=data.get("last_routing_decision"),
            source=data.get("source"),
            organization_id=data.get("organization_id"),
            turns=data.get("turns", []),
            current_turn_events=data.get("current_turn_events", []),
        )

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> "Tracker":
        return cls(
            sender_id=doc["sender_id"],
            assistant_id=doc["assistant_id"],
            events=doc.get("events", []),
            active_flow_state=doc.get("active_flow_state"),
            active_agent_id=doc.get("active_agent_id"),
            active_agent_kind=doc.get("active_agent_kind"),
            last_routing_decision=doc.get("last_routing_decision"),
            source=doc.get("source"),
            organization_id=doc.get("organization_id"),
            turns=doc.get("turns", []),
            current_turn_events=doc.get("current_turn_events", []),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "sender_id": self._sender_id,
            "assistant_id": self._assistant_id,
            "events": self._events,
            "active_flow_state": self._active_flow_state,
            "active_agent_id": self._active_agent_id,
            "active_agent_kind": self._active_agent_kind,
            "last_routing_decision": self._last_routing_decision,
            "source": self._source,
            "organization_id": self._organization_id,
            "turns": self._turns,
            "current_turn_events": self._current_turn_events,
        }

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._events)

    def set_active_flow_state(self, state: dict[str, Any] | None) -> None:
        self._active_flow_state = state

    def enter_workflow(self, *, state: dict[str, Any]) -> None:
        self._active_flow_state = state
        self._active_agent_id = self._assistant_id
        self._active_agent_kind = "workflow"

    def clear_flow_state(self) -> None:
        self._active_flow_state = None
        self._active_agent_id = self._assistant_id
        self._active_agent_kind = "orchestrator"

    def reset_to_orchestrator(self) -> None:
        self._active_agent_id = self._assistant_id
        self._active_agent_kind = "orchestrator"
        self._last_routing_decision = None

    def set_routing_decision(self, *, agent_id: str, kind: str, decision: dict[str, Any] | None) -> None:
        self._active_agent_id = agent_id
        self._active_agent_kind = kind
        self._last_routing_decision = decision

    def append_user_message(self, *, message: str, metadata: dict[str, Any]) -> None:
        self._events.append(
            {
                "role": "user",
                "content": message,
                "metadata": metadata,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    def append_assistant_replies(self, replies: list[str]) -> None:
        now = datetime.now(UTC).isoformat()
        for reply in replies:
            self._events.append(
                {
                    "role": "assistant",
                    "content": reply,
                    "timestamp": now,
                },
            )

    def append_trace_event(self, event: dict[str, Any]) -> None:
        self._current_turn_events.append(event)

    def finish_trace_turn(
        self,
        *,
        turn_id: str,
        started_at: str,
        routing_decision: dict[str, Any] | None,
        turn_evidence: dict[str, Any] | None = None,
    ) -> None:
        turn: dict[str, Any] = {
            "turn_id": turn_id,
            "started_at": started_at,
            "events": list(self._current_turn_events),
            "routing_decision": routing_decision,
        }
        if turn_evidence is not None:
            turn["turn_evidence"] = turn_evidence
        self._turns.append(turn)
        self._current_turn_events = []
