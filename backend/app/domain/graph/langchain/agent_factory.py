from __future__ import annotations

from typing import Any

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.domain.graph.langchain.tool_router import ToolRouterContext, run_search_knowledge_tool
from app.domain.graph.langchain.pii_middleware import build_agent_pii_middleware
from app.domain.graph.search_knowledge_delegate import SEARCH_KNOWLEDGE_TOOL_NAME
from app.domain.graph.sub_agent_delegate import RETURN_TO_ORCHESTRATOR_TOOL_NAME
from app.domain.models.runtime_bundle import RuntimeOrchestrator
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext

MAX_AGENT_MODEL_CALLS = 5
FALLBACK_REPLY = "I couldn't complete that request. Please try again."


def build_chat_model(
    orchestrator: RuntimeOrchestrator,
    *,
    tracing_context: LlmTracingContext | None = None,
) -> ChatBedrockConverse:
    llm_config = orchestrator.llm_config
    return ChatBedrockConverse(
        model_id=llm_config.model_id if llm_config else None,
        region_name=llm_config.region if llm_config else None,
        temperature=orchestrator.temperature,
        max_tokens=orchestrator.max_output_tokens,
    )


def _build_routing_middleware(router: ToolRouterContext) -> Any:
    from langchain.agents.middleware.types import AgentMiddleware, hook_config
    from typing_extensions import override

    class BotBuilderRoutingMiddleware(AgentMiddleware):
        def __init__(self, routing_router: ToolRouterContext) -> None:
            super().__init__()
            self._router = routing_router

        @override
        @hook_config(can_jump_to=["end"])
        async def aafter_model(self, state: dict[str, Any], runtime: Any) -> dict[str, Any] | None:
            messages = state.get("messages", [])
            last_ai: AIMessage | None = None
            for message in reversed(messages):
                if isinstance(message, AIMessage):
                    last_ai = message
                    break
            if last_ai is None or not last_ai.tool_calls:
                return None

            for tool_call in last_ai.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args") or {}
                if tool_name and tool_name in self._router.delegates_by_name:
                    from app.domain.graph.turn_result import DelegationRequest

                    self._router.delegation = DelegationRequest(
                        sub_agent=self._router.delegates_by_name[tool_name],
                        args=tool_args,
                        function_name=tool_name,
                    )
                    return {"jump_to": "end"}
                if tool_name and tool_name in self._router.workflows_by_name:
                    from app.domain.graph.turn_result import WorkflowEnterRequest

                    self._router.workflow_enter = WorkflowEnterRequest(
                        workflow=self._router.workflows_by_name[tool_name],
                        function_name=tool_name,
                        args=tool_args,
                    )
                    return {"jump_to": "end"}
                if (
                    self._router.handle_return_to_orchestrator
                    and tool_name == RETURN_TO_ORCHESTRATOR_TOOL_NAME
                ):
                    self._router.orchestrator_return = True
                    return {"jump_to": "end"}
            return None

        @override
        async def awrap_tool_call(self, request: Any, handler: Any) -> ToolMessage | Any:
            tool_name = request.tool_call.get("name")
            if tool_name != SEARCH_KNOWLEDGE_TOOL_NAME:
                return await handler(request)

            tool_call_id = str(request.tool_call.get("id") or tool_name)
            tool_args = request.tool_call.get("args") or {}
            result_text = await run_search_knowledge_tool(
                tool_args=tool_args,
                knowledge_bases=self._router.knowledge_bases,
                organization_id=self._router.organization_id,
                rag=self._router.rag,
                trace=self._router.trace,
            )
            return ToolMessage(content=str(result_text), tool_call_id=tool_call_id)

    return BotBuilderRoutingMiddleware(router)


def create_bot_agent(
    *,
    orchestrator: RuntimeOrchestrator,
    tools: list[BaseTool],
    system_prompt: str,
    router: ToolRouterContext,
    tracing_context: LlmTracingContext | None = None,
) -> Any:
    from langchain.agents.factory import create_agent
    from langchain.agents.middleware.model_call_limit import ModelCallLimitMiddleware

    model = build_chat_model(orchestrator, tracing_context=tracing_context)
    middleware = [
        *build_agent_pii_middleware(),
        _build_routing_middleware(router),
        ModelCallLimitMiddleware(run_limit=MAX_AGENT_MODEL_CALLS, exit_behavior="end"),
    ]
    return create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware,
    )
