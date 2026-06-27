import re
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.domain.models.runtime_bundle import RuntimeWorkflow


def normalize_workflow_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "workflow"


def workflow_tool_name(name: str) -> str:
    return f"workflow_{normalize_workflow_name(name)}"


class _WorkflowDelegateArgs(BaseModel):
    reason: str | None = Field(
        default=None,
        description="Optional reason for starting this workflow",
    )


def build_workflow_delegate_tools(
    workflows: list[RuntimeWorkflow],
    *,
    reserved_names: set[str],
) -> tuple[list[StructuredTool], dict[str, RuntimeWorkflow]]:
    tools: list[StructuredTool] = []
    by_name: dict[str, RuntimeWorkflow] = {}

    for workflow in workflows:
        function_name = workflow_tool_name(workflow.name)
        if function_name in reserved_names or function_name in by_name:
            continue

        description = workflow.description or f"Start workflow {workflow.name}"

        async def _workflow_stub(**_kwargs: Any) -> str:
            return "Workflow start is handled by the chat runtime."

        tools.append(
            StructuredTool.from_function(
                coroutine=_workflow_stub,
                name=function_name,
                description=description,
                args_schema=_WorkflowDelegateArgs,
            ),
        )
        by_name[function_name] = workflow

    return tools, by_name
