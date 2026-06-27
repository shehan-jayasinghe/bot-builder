from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.domain.models.runtime_bundle import RuntimeWorkflow
from app.domain.workflow.slot_validator import validate_slot_value

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

MAX_CHAIN_STEPS = 10


@dataclass
class WorkflowReply:
    text: str
    buttons: list[dict[str, str]] | None = None


@dataclass
class WorkflowTurnResult:
    replies: list[WorkflowReply] = field(default_factory=list)
    exited: bool = False
    routing: dict[str, Any] = field(default_factory=dict)


class WorkflowRunner:
    def build_initial_state(self, workflow: RuntimeWorkflow) -> dict[str, Any] | None:
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

    async def run_turn(
        self,
        *,
        workflow: RuntimeWorkflow,
        state: dict[str, Any],
        user_message: str,
        trace: TraceCallback | None = None,
    ) -> WorkflowTurnResult:
        replies: list[WorkflowReply] = []
        current_node_id = str(state["current_node_id"])
        slots: dict[str, Any] = dict(state.get("slots") or {})
        awaiting_slot = state.get("awaiting_slot")
        steps = 0

        while steps < MAX_CHAIN_STEPS:
            steps += 1
            node = _find_node(workflow, current_node_id)
            if node is None:
                break

            node_type = str(node.get("type", ""))
            node_data = dict(node.get("data") or {})
            if trace is not None:
                await trace(
                    "workflow_step",
                    {
                        "workflow_id": workflow.id,
                        "node_id": current_node_id,
                        "type": node_type,
                    },
                )

            if node_type == "start":
                next_id = _next_node_id(workflow, current_node_id)
                if next_id is None:
                    break
                current_node_id = next_id
                continue

            if node_type == "message":
                text = _substitute_slots(str(node_data.get("text") or ""), slots)
                buttons = _normalize_buttons(node_data.get("buttons"))
                replies.append(WorkflowReply(text=text, buttons=buttons))
                next_id = _next_node_id(workflow, current_node_id)
                if next_id is None:
                    _apply_flow_state(
                        state,
                        workflow_id=workflow.id,
                        current_node_id=current_node_id,
                        slots=slots,
                        awaiting_slot=awaiting_slot,
                    )
                    return WorkflowTurnResult(
                        replies=replies,
                        exited=True,
                        routing=_workflow_routing(workflow, exited=True),
                    )
                current_node_id = next_id
                next_node = _find_node(workflow, current_node_id)
                if next_node is not None and str(next_node.get("type")) in {"message", "output"}:
                    continue
                break

            if node_type == "input":
                slot_name = _slot_name(node_data)
                if not slot_name:
                    break

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
                        replies.append(WorkflowReply(text=retry_message))
                        break

                    slots[slot_name] = user_message.strip()
                    awaiting_slot = None
                    if trace is not None:
                        await trace("slot_captured", {"slot_name": slot_name})
                    next_id = _next_node_id(workflow, current_node_id)
                    if next_id is None:
                        break
                    current_node_id = next_id
                    continue

                awaiting_slot = slot_name
                prompt = str(
                    node_data.get("prompt")
                    or node_data.get("label")
                    or "Please respond:",
                )
                replies.append(WorkflowReply(text=prompt))
                break

            if node_type == "output":
                text = _substitute_slots(
                    str(node_data.get("text") or node_data.get("label") or ""),
                    slots,
                )
                if text:
                    replies.append(WorkflowReply(text=text))
                next_id = _next_node_id(workflow, current_node_id)
                if next_id is None:
                    _apply_flow_state(
                        state,
                        workflow_id=workflow.id,
                        current_node_id=current_node_id,
                        slots=slots,
                        awaiting_slot=awaiting_slot,
                    )
                    return WorkflowTurnResult(
                        replies=replies,
                        exited=True,
                        routing=_workflow_routing(workflow, exited=True),
                    )
                current_node_id = next_id
                next_node = _find_node(workflow, current_node_id)
                if next_node is not None and str(next_node.get("type")) in {"message", "output"}:
                    continue
                break

            if node_type == "end":
                farewell = node_data.get("text")
                if farewell:
                    replies.append(
                        WorkflowReply(text=_substitute_slots(str(farewell), slots)),
                    )
                _apply_flow_state(
                    state,
                    workflow_id=workflow.id,
                    current_node_id=current_node_id,
                    slots=slots,
                    awaiting_slot=awaiting_slot,
                )
                return WorkflowTurnResult(
                    replies=replies,
                    exited=True,
                    routing=_workflow_routing(workflow, exited=True),
                )

            next_id = _next_node_id(workflow, current_node_id)
            if next_id is None:
                break
            current_node_id = next_id

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
            routing=_workflow_routing(
                workflow,
                exited=False,
                current_node_id=current_node_id,
            ),
        )


def _apply_flow_state(
    state: dict[str, Any],
    *,
    workflow_id: str,
    current_node_id: str,
    slots: dict[str, Any],
    awaiting_slot: Any,
) -> None:
    state.update(
        {
            "workflow_id": workflow_id,
            "current_node_id": current_node_id,
            "slots": slots,
            "awaiting_slot": awaiting_slot,
        },
    )


def _workflow_routing(
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
