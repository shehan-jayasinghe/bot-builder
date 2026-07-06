from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.domain.graph.search_knowledge_delegate import (
    SEARCH_KNOWLEDGE_TOOL_NAME,
    execute_search_knowledge,
)
from app.domain.graph.turn_result import DelegationRequest, WorkflowEnterRequest
from app.domain.models.runtime_bundle import RuntimeSubAgent, RuntimeTool, RuntimeWorkflow

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

    from app.domain.pipeline.rag.retriever import RAGRetriever

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass
class ToolRouterContext:
    delegates_by_name: dict[str, RuntimeSubAgent] = field(default_factory=dict)
    workflows_by_name: dict[str, RuntimeWorkflow] = field(default_factory=dict)
    knowledge_bases: list[Any] = field(default_factory=list)
    organization_id: str = ""
    rag: RAGRetriever | None = None
    trace: TraceCallback | None = None
    handle_return_to_orchestrator: bool = False
    delegation: DelegationRequest | None = None
    workflow_enter: WorkflowEnterRequest | None = None
    orchestrator_return: bool = False


async def run_search_knowledge_tool(
    *,
    tool_args: dict[str, Any],
    knowledge_bases: list[Any],
    organization_id: str,
    rag: RAGRetriever | None,
    trace: TraceCallback | None,
) -> str:
    query = str(tool_args.get("query") or "")
    kb_names = tool_args.get("knowledge_base_names")
    scoped_names = kb_names if isinstance(kb_names, list) else None

    if trace is not None:
        await trace(
            "tool_start",
            {
                "tool_name": SEARCH_KNOWLEDGE_TOOL_NAME,
                "arguments": tool_args,
            },
        )

    if rag is None or not knowledge_bases:
        result_text = "Knowledge search is not available."
        if trace is not None:
            await trace(
                "tool_complete",
                {
                    "tool_name": SEARCH_KNOWLEDGE_TOOL_NAME,
                    "context_length": 0,
                    "kb_ids": [],
                    "chunk_count": 0,
                },
            )
        return result_text

    rag_result = await execute_search_knowledge(
        rag=rag,
        query=query,
        knowledge_bases=knowledge_bases,
        organization_id=organization_id,
        knowledge_base_names=scoped_names,
    )
    if rag_result.error and not rag_result.context:
        result_text = rag_result.error
    else:
        result_text = rag_result.context or "No relevant knowledge found."

    if trace is not None:
        trace_data: dict[str, object] = {
            "tool_name": SEARCH_KNOWLEDGE_TOOL_NAME,
            "context_length": len(rag_result.context),
            "kb_ids": rag_result.kb_ids,
            "chunk_count": rag_result.chunk_count,
            "storage_types": rag_result.storage_types,
        }
        if rag_result.error:
            trace_data["partial_error"] = rag_result.error
        await trace("tool_complete", trace_data)

    return result_text


def build_executor_langgraph_tools(
    tools: list[RuntimeTool],
    *,
    connectors_by_id: dict[str, dict[str, Any]],
    search_knowledge_tool: BaseTool | None,
) -> list[BaseTool]:
    from app.domain.executors.langgraph_tools import build_langgraph_tools

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for tool in tools:
        if search_knowledge_tool is not None and tool.name == SEARCH_KNOWLEDGE_TOOL_NAME:
            continue
        connector = connectors_by_id.get(tool.connector_id)
        if connector is None:
            continue
        pairs.append(
            (
                {
                    "name": tool.name,
                    "description": tool.description,
                    "executor": tool.executor,
                    "config": tool.config,
                },
                connector,
            ),
        )

    langgraph_tools = build_langgraph_tools(pairs)
    if search_knowledge_tool is not None:
        langgraph_tools.append(search_knowledge_tool)
    return langgraph_tools
