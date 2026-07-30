from typing import TYPE_CHECKING, Any, Awaitable, Callable

from langchain_core.tools import BaseTool

from app.domain.constants.chat_constants import MAX_HISTORY_TURNS
from app.domain.graph.langchain.tool_router import run_search_knowledge_tool
from app.domain.graph.search_knowledge_delegate import (
    SEARCH_KNOWLEDGE_TOOL_NAME,
    build_search_knowledge_tool,
)
from app.domain.graph.sub_agent_delegate import (
    SubAgentRunner,
    build_delegate_langgraph_tools,
)
from app.domain.graph.turn_evidence import TurnEvidence
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeSubAgent, RuntimeTool, RuntimeWorkflow
from app.domain.models.tracker import Tracker
from app.domain.workflow.workflow_delegate import build_workflow_delegate_tools
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext

if TYPE_CHECKING:
    from app.domain.pipeline.rag.retriever import RAGRetriever

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


class OrchestratorRunner:
    """Runs orchestrator LLM turns via LangChain create_agent()."""

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
        turn_evidence: TurnEvidence | None = None,
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
            turn_evidence=turn_evidence,
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
            turn_evidence=turn_evidence,
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
        turn_evidence: TurnEvidence | None = None,
    ) -> AgentTurnResult:
        from app.domain.graph.langchain.orchestrator_agent import run_tool_agent_turn

        return await run_tool_agent_turn(
            orchestrator=orchestrator,
            system_prompt=system_prompt,
            history=history,
            tools=tools,
            connectors_by_id=connectors_by_id,
            search_knowledge_tool=search_knowledge_tool,
            knowledge_bases=knowledge_bases,
            organization_id=organization_id,
            delegate_tools=delegate_tools,
            delegates_by_name=delegates_by_name,
            workflow_tools=workflow_tools,
            workflows_by_name=workflows_by_name,
            return_to_orchestrator_tool=return_to_orchestrator_tool,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
            turn_evidence=turn_evidence,
        )

    _run_search_knowledge_tool = staticmethod(run_search_knowledge_tool)


def _cap_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(history) <= MAX_HISTORY_TURNS:
        return list(history)
    return list(history[-MAX_HISTORY_TURNS:])
