from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.domain.models.runtime_bundle import RuntimeWorkflow
from app.domain.workflow.workflow_graph_compiler import (
    build_initial_state,
    compile_workflow_graph,
    workflow_routing,
)

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass
class WorkflowReply:
    text: str
    buttons: list[dict[str, str]] | None = None


@dataclass
class WorkflowTurnResult:
    replies: list[WorkflowReply] = field(default_factory=list)
    exited: bool = False
    routing: dict[str, Any] = field(default_factory=dict)


class WorkflowGraphRunner:
    def __init__(self) -> None:
        self._compiled_graphs: dict[str, Any] = {}

    def build_initial_state(self, workflow: RuntimeWorkflow) -> dict[str, Any] | None:
        return build_initial_state(workflow)

    async def run_turn(
        self,
        *,
        workflow: RuntimeWorkflow,
        state: dict[str, Any],
        user_message: str,
        trace: TraceCallback | None = None,
    ) -> WorkflowTurnResult:
        compiled = self._get_compiled_graph(workflow)
        current_node_id = str(state["current_node_id"])

        if trace is not None:
            await trace(
                "workflow_step",
                {
                    "workflow_id": workflow.id,
                    "node_id": current_node_id,
                    "engine": "langgraph",
                },
            )

        graph_state = {
            "current_node_id": current_node_id,
            "slots": dict(state.get("slots") or {}),
            "awaiting_slot": state.get("awaiting_slot"),
            "user_message": user_message,
            "replies": [],
            "steps": 0,
            "exited": False,
            "should_continue": True,
        }

        result_state = await compiled.ainvoke(graph_state)

        replies = [
            WorkflowReply(
                text=str(item.get("text") or ""),
                buttons=item.get("buttons"),
            )
            for item in result_state.get("replies") or []
            if item.get("text")
        ]

        exited = bool(result_state.get("exited"))
        current_node_id = str(result_state.get("current_node_id") or current_node_id)
        slots = dict(result_state.get("slots") or {})
        awaiting_slot = result_state.get("awaiting_slot")

        if trace is not None and awaiting_slot is None and any(
            slot_name in slots for slot_name in slots
        ):
            for slot_name in slots:
                if slot_name not in (state.get("slots") or {}):
                    await trace("slot_captured", {"slot_name": slot_name})

        state.update(
            {
                "workflow_id": workflow.id,
                "current_node_id": current_node_id,
                "slots": slots,
                "awaiting_slot": awaiting_slot,
            },
        )

        return WorkflowTurnResult(
            replies=replies,
            exited=exited,
            routing=workflow_routing(
                workflow,
                exited=exited,
                current_node_id=None if exited else current_node_id,
            ),
        )

    def _get_compiled_graph(self, workflow: RuntimeWorkflow) -> Any:
        cache_key = str(workflow.id)
        compiled = self._compiled_graphs.get(cache_key)
        if compiled is None:
            compiled = compile_workflow_graph(workflow)
            self._compiled_graphs[cache_key] = compiled
        return compiled
