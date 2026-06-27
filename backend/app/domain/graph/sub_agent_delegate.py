import re
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from app.domain.constants.chat_constants import MAX_HISTORY_TURNS
from app.domain.graph.search_knowledge_delegate import SEARCH_KNOWLEDGE_TOOL_NAME, build_search_knowledge_tool
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeSubAgent, RuntimeTool
from app.domain.models.tracker import Tracker
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext

_PARAM_TYPE_MAP: dict[str, type] = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
}


def normalize_sub_agent_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "sub_agent"


def build_delegate_args_schema(sub_agent: RuntimeSubAgent) -> type[BaseModel] | None:
    if not sub_agent.parameters:
        return create_model(
            f"{normalize_sub_agent_name(sub_agent.name)}_delegate_args",
            query=(str, Field(description="Task or question for the sub-agent")),
        )

    fields: dict[str, Any] = {}
    for param in sub_agent.parameters:
        py_type = _PARAM_TYPE_MAP.get(param.type, str)
        description = param.description or param.name
        if param.required:
            fields[param.name] = (py_type, Field(description=description))
        else:
            fields[param.name] = (py_type | None, Field(default=None, description=description))

    model_name = f"{normalize_sub_agent_name(sub_agent.name)}_delegate_args"
    return create_model(model_name, **fields)  # type: ignore[call-overload]


def build_delegate_langgraph_tools(
    sub_agents: list[RuntimeSubAgent],
    *,
    reserved_names: set[str],
) -> tuple[list[StructuredTool], dict[str, RuntimeSubAgent]]:
    tools: list[StructuredTool] = []
    by_name: dict[str, RuntimeSubAgent] = {}

    for sub_agent in sub_agents:
        function_name = normalize_sub_agent_name(sub_agent.name)
        if function_name in reserved_names or function_name in by_name:
            continue

        description = sub_agent.description or f"Delegate to sub-agent {sub_agent.name}"
        args_schema = build_delegate_args_schema(sub_agent)

        async def _delegate_stub(**_kwargs: Any) -> str:
            return "Delegation is handled by the chat runtime."

        tools.append(
            StructuredTool.from_function(
                coroutine=_delegate_stub,
                name=function_name,
                description=description,
                args_schema=args_schema,
            ),
        )
        by_name[function_name] = sub_agent

    return tools, by_name


def format_delegate_context(delegate_args: dict[str, Any]) -> str:
    if not delegate_args:
        return ""
    lines = [f"- {key}: {value}" for key, value in delegate_args.items()]
    return "## Delegation context\n" + "\n".join(lines)


def build_sub_agent_system_prompt(
    sub_agent: RuntimeSubAgent,
    *,
    delegate_args: dict[str, Any],
) -> str:
    parts = [sub_agent.instructions]
    delegate_context = format_delegate_context(delegate_args)
    if delegate_context:
        parts.append(delegate_context)
    return "\n\n".join(parts)


class SubAgentRunner:
    """Runs a scoped LLM turn for a delegated sub-agent."""

    def __init__(self, *, tool_executor: Any) -> None:
        self._tool_executor = tool_executor

    async def run_turn(
        self,
        *,
        sub_agent: RuntimeSubAgent,
        orchestrator: RuntimeOrchestrator,
        tracker: Tracker,
        delegate_args: dict[str, Any],
        bundle: RuntimeBundle,
        connectors_by_id: dict[str, dict[str, Any]],
        tracing_context: LlmTracingContext | None = None,
        rag: Any = None,
        trace: Any = None,
    ) -> list[str]:
        system_prompt = build_sub_agent_system_prompt(
            sub_agent,
            delegate_args=delegate_args,
        )
        search_knowledge_tool = build_search_knowledge_tool(
            sub_agent.knowledge_bases,
            capability_catalog=bundle.capability_catalog,
        )
        scoped_tools = [
            tool for tool in sub_agent.tools
            if not (search_knowledge_tool is not None and tool.name == SEARCH_KNOWLEDGE_TOOL_NAME)
        ]
        history = _cap_history(tracker.get_history())
        result = await self._tool_executor.execute_tool_turn(
            orchestrator=orchestrator,
            system_prompt=system_prompt,
            history=history,
            tools=scoped_tools,
            search_knowledge_tool=search_knowledge_tool,
            knowledge_bases=sub_agent.knowledge_bases,
            organization_id=bundle.organization_id,
            delegate_tools=[],
            delegates_by_name={},
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
        )
        return result.replies


def _cap_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(history) <= MAX_HISTORY_TURNS:
        return list(history)
    return list(history[-MAX_HISTORY_TURNS:])
