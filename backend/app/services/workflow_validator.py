from typing import Any

from app.shared.exceptions.workflow import WorkflowValidationError


def validate_workflow_for_publish(*, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    if not nodes:
        raise WorkflowValidationError("Workflow must have at least one node")

    node_ids = {str(node["id"]) for node in nodes}
    start_nodes = [node for node in nodes if node.get("type") == "start"]

    if len(start_nodes) != 1:
        raise WorkflowValidationError("Workflow must have exactly one start node")

    start_id = str(start_nodes[0]["id"])
    if len(nodes) < 2:
        raise WorkflowValidationError("Workflow must have at least one step after start")

    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        if source not in node_ids:
            raise WorkflowValidationError(f"Edge references unknown source node: {source}")
        if target not in node_ids:
            raise WorkflowValidationError(f"Edge references unknown target node: {target}")

    if not any(str(edge["source"]) == start_id for edge in edges):
        raise WorkflowValidationError("Start node must connect to at least one step")
