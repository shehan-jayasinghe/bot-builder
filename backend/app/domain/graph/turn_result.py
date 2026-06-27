from dataclasses import dataclass, field
from typing import Any

from app.domain.models.runtime_bundle import RuntimeSubAgent, RuntimeWorkflow


@dataclass(frozen=True)
class DelegationRequest:
    sub_agent: RuntimeSubAgent
    args: dict[str, Any]
    function_name: str


@dataclass(frozen=True)
class WorkflowEnterRequest:
    workflow: RuntimeWorkflow
    function_name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class AgentTurnResult:
    replies: list[str]
    routing: dict[str, Any] = field(default_factory=lambda: {"mode": "orchestrator"})
    delegation: DelegationRequest | None = None
    workflow_enter: WorkflowEnterRequest | None = None
