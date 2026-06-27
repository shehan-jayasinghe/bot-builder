from typing import TYPE_CHECKING, Any, Awaitable, Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.domain.constants.chat_constants import MAX_HISTORY_TURNS
from app.domain.executors.langgraph_tools import build_langgraph_tools
from app.domain.graph.search_knowledge_delegate import (
    SEARCH_KNOWLEDGE_TOOL_NAME,
    build_search_knowledge_tool,
    execute_search_knowledge,
)
from app.domain.graph.sub_agent_delegate import (
    SubAgentRunner,
    build_delegate_langgraph_tools,
)
from app.domain.graph.turn_result import AgentTurnResult, DelegationRequest, WorkflowEnterRequest
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeSubAgent, RuntimeTool, RuntimeWorkflow
from app.domain.models.tracker import Tracker
from app.domain.workflow.workflow_delegate import build_workflow_delegate_tools
from app.infrastructure.ai.langsmith_tracing import build_llm_run_config, LlmTracingContext
from app.infrastructure.ai.llm import BedrockLLM

if TYPE_CHECKING:
    from app.domain.pipeline.rag.retriever import RAGRetriever

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

MAX_TOOL_ITERATIONS = 5


class OrchestratorRunner:
    """Runs orchestrator LLM turns with optional tool calling and sub-agent delegation."""

    async def run_turn(
        self,
        *,
        bundle: RuntimeBundle,
        tracker: Tracker,
        user_message: str,
        system_prompt: str,
        connectors_by_id: dict[str, dict[str, Any]],
        tracing_context: LlmTracingContext | None = None,
        rag: "RAGRetriever | None" = None,
        trace: TraceCallback | None = None,
    ) -> AgentTurnResult:
        orchestrator = bundle.orchestrator
        history = _cap_history(tracker.get_history())

        reserved_names = {tool.name for tool in orchestrator.tools}
        reserved_names.add(SEARCH_KNOWLEDGE_TOOL_NAME)
        delegate_tools, delegates_by_name = build_delegate_langgraph_tools(
            orchestrator.sub_agents,
            reserved_names=reserved_names,
        )
        reserved_names.update(delegates_by_name)
        workflow_tools, workflows_by_name = build_workflow_delegate_tools(
            orchestrator.workflows,
            reserved_names=reserved_names,
            capability_catalog=bundle.capability_catalog,
        )
        search_knowledge_tool = build_search_knowledge_tool(
            orchestrator.knowledge_bases,
            capability_catalog=bundle.capability_catalog,
        )

        has_executor_tools = bool(orchestrator.tools)
        has_delegates = bool(delegate_tools)
        has_workflows = bool(workflow_tools)
        has_search_knowledge = search_knowledge_tool is not None

        if not has_executor_tools and not has_delegates and not has_workflows and not has_search_knowledge:
            reply = await self._simple_chat(
                orchestrator=orchestrator,
                system_prompt=system_prompt,
                history=history,
                tracing_context=tracing_context,
            )
            return AgentTurnResult(replies=[reply])

        result = await self.execute_tool_turn(
            orchestrator=orchestrator,
            system_prompt=system_prompt,
            history=history,
            tools=orchestrator.tools,
            search_knowledge_tool=search_knowledge_tool,
            knowledge_bases=orchestrator.knowledge_bases,
            organization_id=bundle.organization_id,
            delegate_tools=delegate_tools,
            delegates_by_name=delegates_by_name,
            workflow_tools=workflow_tools,
            workflows_by_name=workflows_by_name,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
        )
        if result.workflow_enter is not None:
            return result
        if result.delegation is None:
            return result

        delegation = result.delegation
        sub_runner = SubAgentRunner(tool_executor=self)
        sub_result = await sub_runner.run_turn(
            sub_agent=delegation.sub_agent,
            orchestrator=orchestrator,
            tracker=tracker,
            delegate_args=delegation.args,
            bundle=bundle,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
        )
        if sub_result.orchestrator_return:
            return sub_result
        routing = {
            "mode": "delegate",
            "type": "delegate",
            "sub_agent_id": delegation.sub_agent.id,
            "sub_agent_name": delegation.sub_agent.name,
            "args": delegation.args,
        }
        return AgentTurnResult(replies=sub_result.replies, routing=routing)

    async def execute_tool_turn(
        self,
        *,
        orchestrator: RuntimeOrchestrator,
        system_prompt: str,
        history: list[dict[str, Any]],
        tools: list[RuntimeTool],
        connectors_by_id: dict[str, dict[str, Any]],
        search_knowledge_tool: BaseTool | None = None,
        knowledge_bases: list | None = None,
        organization_id: str = "",
        delegate_tools: list[BaseTool] | None = None,
        delegates_by_name: dict[str, RuntimeSubAgent] | None = None,
        workflow_tools: list[BaseTool] | None = None,
        workflows_by_name: dict[str, RuntimeWorkflow] | None = None,
        return_to_orchestrator_tool: BaseTool | None = None,
        tracing_context: LlmTracingContext | None = None,
        rag: "RAGRetriever | None" = None,
        trace: TraceCallback | None = None,
    ) -> AgentTurnResult:
        delegate_tools = delegate_tools or []
        delegates_by_name = delegates_by_name or {}
        workflow_tools = workflow_tools or []
        workflows_by_name = workflows_by_name or {}
        knowledge_bases = knowledge_bases or []

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
        langgraph_tools.extend(delegate_tools)
        langgraph_tools.extend(workflow_tools)
        if return_to_orchestrator_tool is not None:
            langgraph_tools.append(return_to_orchestrator_tool)
        if not langgraph_tools:
            reply = await self._simple_chat(
                orchestrator=orchestrator,
                system_prompt=system_prompt,
                history=history,
                tracing_context=tracing_context,
            )
            return AgentTurnResult(replies=[reply])

        tools_by_name = {tool.name: tool for tool in langgraph_tools}
        llm = self._build_llm(orchestrator, tracing_context=tracing_context).get_client().bind_tools(
            langgraph_tools,
        )
        run_config = build_llm_run_config(tracing_context)

        messages: list[SystemMessage | HumanMessage | AIMessage | ToolMessage] = [
            SystemMessage(content=system_prompt),
        ]
        for turn in history:
            role = turn.get("role")
            content = str(turn.get("content", ""))
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        for _ in range(MAX_TOOL_ITERATIONS):
            if run_config:
                response = await llm.ainvoke(messages, config=run_config)
            else:
                response = await llm.ainvoke(messages)
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                return AgentTurnResult(replies=[str(response.content)])

            messages.append(response)
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args") or {}
                tool_call_id = str(tool_call.get("id") or tool_name)

                if tool_name and tool_name in delegates_by_name:
                    return AgentTurnResult(
                        replies=[],
                        delegation=DelegationRequest(
                            sub_agent=delegates_by_name[tool_name],
                            args=tool_args,
                            function_name=tool_name,
                        ),
                    )

                if tool_name and tool_name in workflows_by_name:
                    return AgentTurnResult(
                        replies=[],
                        workflow_enter=WorkflowEnterRequest(
                            workflow=workflows_by_name[tool_name],
                            function_name=tool_name,
                            args=tool_args,
                        ),
                    )

                if (
                    return_to_orchestrator_tool is not None
                    and tool_name == return_to_orchestrator_tool.name
                ):
                    return AgentTurnResult(replies=[], orchestrator_return=True)

                if tool_name == SEARCH_KNOWLEDGE_TOOL_NAME:
                    tool_result = await self._run_search_knowledge_tool(
                        tool_args=tool_args,
                        knowledge_bases=knowledge_bases,
                        organization_id=organization_id,
                        rag=rag,
                        trace=trace,
                    )
                elif not tool_name or tool_name not in tools_by_name:
                    tool_result = f"Unknown tool: {tool_name}"
                else:
                    tool_result = await tools_by_name[tool_name].ainvoke(tool_args)

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id,
                    ),
                )

        return AgentTurnResult(replies=["I couldn't complete that request. Please try again."])

    @staticmethod
    async def _run_search_knowledge_tool(
        *,
        tool_args: dict[str, Any],
        knowledge_bases: list,
        organization_id: str,
        rag: "RAGRetriever | None",
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

    @staticmethod
    def _build_llm(
        orchestrator: RuntimeOrchestrator,
        *,
        tracing_context: LlmTracingContext | None = None,
    ) -> BedrockLLM:
        llm_config = orchestrator.llm_config
        return BedrockLLM(
            model_id=llm_config.model_id if llm_config else None,
            region=llm_config.region if llm_config else None,
            temperature=orchestrator.temperature,
            max_output_tokens=orchestrator.max_output_tokens,
            tracing_context=tracing_context,
        )

    async def _simple_chat(
        self,
        *,
        orchestrator: RuntimeOrchestrator,
        system_prompt: str,
        history: list[dict[str, Any]],
        tracing_context: LlmTracingContext | None = None,
    ) -> str:
        llm = self._build_llm(orchestrator, tracing_context=tracing_context)
        return await llm.chat_from_history(system_prompt=system_prompt, history=history)


def _cap_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(history) <= MAX_HISTORY_TURNS:
        return list(history)
    return list(history[-MAX_HISTORY_TURNS:])
