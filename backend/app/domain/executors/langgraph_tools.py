import json
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field, create_model

from app.domain.constants.executor_constants import EXECUTOR_CONNECTOR_TYPES
from app.domain.executors.context import ExecutorContext
from app.domain.executors.errors import ConnectorConfigError
from app.domain.executors.registry import run_executor
from app.domain.executors.template import extract_placeholder_names


def _connector_type(connector: dict[str, Any]) -> str:
    connector_type = connector.get("type")
    if not connector_type:
        raise ConnectorConfigError("Connector missing type")
    return str(connector_type)


def validate_tool_connector_pair(tool: dict[str, Any], connector: dict[str, Any]) -> None:
    executor = tool["executor"]
    expected = EXECUTOR_CONNECTOR_TYPES.get(executor)
    if expected is None:
        raise ConnectorConfigError(f"Unsupported executor: {executor}")
    actual = _connector_type(connector)
    if actual != expected:
        raise ConnectorConfigError(
            f"Executor {executor} requires connector type {expected}, got {actual}"
        )


def _build_args_schema(tool_name: str, tool_config: dict[str, Any]) -> type[BaseModel] | None:
    arg_names = sorted(extract_placeholder_names(tool_config))
    if not arg_names:
        return None
    fields = {
        name: (str, Field(description=f"Value for template {{{{{name}}}}}")) for name in arg_names
    }
    model_name = f"{tool_name}_args".replace("-", "_")
    return create_model(model_name, **fields)  # type: ignore[call-overload]


def build_langgraph_tool(tool: dict[str, Any], connector: dict[str, Any]) -> StructuredTool:
    """Build one LangGraph-compatible tool from a tool doc + connector doc."""
    validate_tool_connector_pair(tool, connector)

    tool_name = tool["name"]
    description = tool.get("description") or tool_name
    executor = tool["executor"]
    tool_config = tool.get("config") or {}
    args_schema = _build_args_schema(tool_name, tool_config)

    async def _coroutine(**kwargs: Any) -> str:
        ctx = ExecutorContext(
            executor=executor,
            connector=connector,
            tool_config=tool_config,
            args=kwargs,
        )
        result = await run_executor(ctx)
        return json.dumps(result, default=str)

    return StructuredTool.from_function(
        coroutine=_coroutine,
        name=tool_name,
        description=description,
        args_schema=args_schema,
    )


def build_langgraph_tools(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[BaseTool]:
    return [build_langgraph_tool(tool, connector) for tool, connector in pairs]


def build_tool_node(pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> ToolNode:
    """LangGraph ToolNode ready to wire into a graph."""
    return ToolNode(build_langgraph_tools(pairs))
