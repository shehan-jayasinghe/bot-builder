from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.domain.models.runtime_bundle import RuntimeWorkflow
from app.domain.workflow.slot_validator import validate_slot_value

MAX_CHAIN_STEPS = 10


class WorkflowGraphState(TypedDict, total=False):
    current_node_id: str
    slots: dict[str, Any]
    awaiting_slot: str | None
    user_message: str
    replies: list[dict[str, Any]]
    steps: int
    exited: bool
    should_continue: bool


def compile_workflow_graph(workflow: RuntimeWorkflow) -> Any:
    """Compile workflow JSON nodes/edges into a LangGraph StateGraph."""

    async def step_node(state: WorkflowGraphState) -> WorkflowGraphState:
        current_node_id = str(state["current_node_id"])
        slots: dict[str, Any] = dict(state.get("slots") or {})
        awaiting_slot = state.get("awaiting_slot")
        user_message = str(state.get("user_message") or "")
        replies = list(state.get("replies") or [])
        steps = int(state.get("steps") or 0) + 1
        exited = bool(state.get("exited"))
        should_continue = False

        if steps > MAX_CHAIN_STEPS or exited:
            return {
                "current_node_id": current_node_id,
                "slots": slots,
                "awaiting_slot": awaiting_slot,
                "replies": replies,
                "steps": steps,
                "exited": exited,
                "should_continue": False,
            }

        node = _find_node(workflow, current_node_id)
        if node is None:
            return {
                "current_node_id": current_node_id,
                "slots": slots,
                "awaiting_slot": awaiting_slot,
                "replies": replies,
                "steps": steps,
                "exited": exited,
                "should_continue": False,
            }

        node_type = str(node.get("type", ""))
        node_data = dict(node.get("data") or {})

        if node_type == "start":
            next_id = _next_node_id(workflow, current_node_id)
            if next_id is None:
                return _pause_state(
                    current_node_id,
                    slots,
                    awaiting_slot,
                    replies,
                    steps,
                )
            return _continue_state(
                next_id,
                slots,
                awaiting_slot,
                replies,
                steps,
                user_message,
            )

        if node_type == "message":
            text = _substitute_slots(str(node_data.get("text") or ""), slots)
            buttons = _normalize_buttons(node_data.get("buttons"))
            replies.append({"text": text, "buttons": buttons})
            next_id = _next_node_id(workflow, current_node_id)
            if next_id is None:
                return {
                    "current_node_id": current_node_id,
                    "slots": slots,
                    "awaiting_slot": awaiting_slot,
                    "replies": replies,
                    "steps": steps,
                    "exited": True,
                    "should_continue": False,
                }
            next_node = _find_node(workflow, next_id)
            if next_node is not None and str(next_node.get("type")) in {"message", "output"}:
                return _continue_state(
                    next_id,
                    slots,
                    awaiting_slot,
                    replies,
                    steps,
                    user_message,
                )
            return _pause_state(next_id, slots, awaiting_slot, replies, steps)

        if node_type == "input":
            slot_name = _slot_name(node_data)
            if not slot_name:
                return _pause_state(current_node_id, slots, awaiting_slot, replies, steps)

            if awaiting_slot == slot_name:
                is_valid, _ = validate_slot_value(
                    user_message,
                    validation=node_data.get("validation"),
                    input_mode=node_data.get("input_mode"),
                    options=node_data.get("options"),
                )
                if not is_valid:
                    retry_message = str(
                        node_data.get("retry_message")
                        or "That doesn't look valid. Please try again.",
                    )
                    replies.append({"text": retry_message, "buttons": None})
                    return _pause_state(current_node_id, slots, awaiting_slot, replies, steps)

                slots[slot_name] = user_message.strip()
                awaiting_slot = None
                next_id = _next_node_id(workflow, current_node_id)
                if next_id is None:
                    return _pause_state(current_node_id, slots, awaiting_slot, replies, steps)
                return _continue_state(
                    next_id,
                    slots,
                    awaiting_slot,
                    replies,
                    steps,
                    user_message,
                )

            awaiting_slot = slot_name
            prompt = str(
                node_data.get("prompt")
                or node_data.get("label")
                or "Please respond:",
            )
            replies.append({"text": prompt, "buttons": None})
            return _pause_state(current_node_id, slots, awaiting_slot, replies, steps)

        if node_type == "output":
            text = _substitute_slots(
                str(node_data.get("text") or node_data.get("label") or ""),
                slots,
            )
            if text:
                replies.append({"text": text, "buttons": None})
            next_id = _next_node_id(workflow, current_node_id)
            if next_id is None:
                return {
                    "current_node_id": current_node_id,
                    "slots": slots,
                    "awaiting_slot": awaiting_slot,
                    "replies": replies,
                    "steps": steps,
                    "exited": True,
                    "should_continue": False,
                }
            next_node = _find_node(workflow, next_id)
            if next_node is not None and str(next_node.get("type")) in {"message", "output"}:
                return _continue_state(
                    next_id,
                    slots,
                    awaiting_slot,
                    replies,
                    steps,
                    user_message,
                )
            return _pause_state(next_id, slots, awaiting_slot, replies, steps)

        if node_type == "end":
            farewell = node_data.get("text")
            if farewell:
                replies.append(
                    {
                        "text": _substitute_slots(str(farewell), slots),
                        "buttons": None,
                    },
                )
            return {
                "current_node_id": current_node_id,
                "slots": slots,
                "awaiting_slot": awaiting_slot,
                "replies": replies,
                "steps": steps,
                "exited": True,
                "should_continue": False,
            }

        next_id = _next_node_id(workflow, current_node_id)
        if next_id is None:
            return _pause_state(current_node_id, slots, awaiting_slot, replies, steps)
        return _continue_state(next_id, slots, awaiting_slot, replies, steps, user_message)

    def _route_after_step(state: WorkflowGraphState) -> str:
        if state.get("exited") or not state.get("should_continue"):
            return END
        if int(state.get("steps") or 0) >= MAX_CHAIN_STEPS:
            return END
        return "step"

    graph = StateGraph(WorkflowGraphState)
    graph.add_node("step", step_node)
    graph.add_conditional_edges("step", _route_after_step, {"step": "step", END: END})
    graph.set_entry_point("step")
    return graph.compile()


def build_initial_state(workflow: RuntimeWorkflow) -> dict[str, Any] | None:
    start_node = _find_start_node(workflow)
    if start_node is None:
        return None

    next_node_id = _next_node_id(workflow, str(start_node["id"]))
    if next_node_id is None:
        return None

    return {
        "workflow_id": workflow.id,
        "current_node_id": next_node_id,
        "slots": {},
        "awaiting_slot": None,
    }


def workflow_routing(
    workflow: RuntimeWorkflow,
    *,
    exited: bool,
    current_node_id: str | None = None,
) -> dict[str, Any]:
    routing: dict[str, Any] = {
        "mode": "workflow",
        "type": "workflow",
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
    }
    if exited:
        routing["exited"] = True
    elif current_node_id is not None:
        routing["current_node_id"] = current_node_id
    return routing


def _continue_state(
    next_node_id: str,
    slots: dict[str, Any],
    awaiting_slot: str | None,
    replies: list[dict[str, Any]],
    steps: int,
    user_message: str,
) -> WorkflowGraphState:
    return {
        "current_node_id": next_node_id,
        "slots": slots,
        "awaiting_slot": awaiting_slot,
        "replies": replies,
        "steps": steps,
        "user_message": user_message,
        "exited": False,
        "should_continue": True,
    }


def _pause_state(
    current_node_id: str,
    slots: dict[str, Any],
    awaiting_slot: str | None,
    replies: list[dict[str, Any]],
    steps: int,
) -> WorkflowGraphState:
    return {
        "current_node_id": current_node_id,
        "slots": slots,
        "awaiting_slot": awaiting_slot,
        "replies": replies,
        "steps": steps,
        "exited": False,
        "should_continue": False,
    }


def _find_start_node(workflow: RuntimeWorkflow) -> dict[str, Any] | None:
    for node in workflow.nodes:
        if node.get("type") == "start":
            return node
    return None


def _find_node(workflow: RuntimeWorkflow, node_id: str) -> dict[str, Any] | None:
    for node in workflow.nodes:
        if str(node.get("id")) == node_id:
            return node
    return None


def _next_node_id(workflow: RuntimeWorkflow, current_node_id: str) -> str | None:
    for edge in workflow.edges:
        if str(edge.get("source")) == current_node_id:
            return str(edge.get("target"))
    return None


def _slot_name(node_data: dict[str, Any]) -> str | None:
    raw = node_data.get("slot_name") or node_data.get("slot")
    if raw is None:
        return None
    name = str(raw).strip()
    return name or None


def _substitute_slots(text: str, slots: dict[str, Any]) -> str:
    result = text
    for key, value in slots.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def _normalize_buttons(raw: Any) -> list[dict[str, str]] | None:
    if not isinstance(raw, list) or not raw:
        return None

    buttons: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("label") or "").strip()
        payload = str(item.get("payload") or item.get("value") or title).strip()
        if title:
            buttons.append({"title": title, "payload": payload})
    return buttons or None
