from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage

from app.domain.graph.langchain.agent_factory import FALLBACK_REPLY, create_bot_agent
from app.domain.graph.langchain.pii_middleware import PII_BLOCKED_USER_MESSAGE
from app.domain.graph.langchain.tool_router import ToolRouterContext, build_executor_langgraph_tools
from app.domain.graph.turn_evidence import TurnEvidence
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import RuntimeOrchestrator, RuntimeTool
from app.infrastructure.ai.langsmith_tracing import build_llm_run_config, LlmTracingContext
from app.infrastructure.ai.llm import BedrockLLM

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

    from app.domain.pipeline.rag.retriever import RAGRetriever


async def run_tool_agent_turn(
    *,
    orchestrator: RuntimeOrchestrator,
    system_prompt: str,
    history: list[dict[str, Any]],
    tools: list[RuntimeTool],
    connectors_by_id: dict[str, dict[str, Any]],
    langgraph_tools: list[BaseTool] | None = None,
    search_knowledge_tool: BaseTool | None = None,
    knowledge_bases: list | None = None,
    organization_id: str = "",
    delegate_tools: list[BaseTool] | None = None,
    delegates_by_name: dict | None = None,
    workflow_tools: list[BaseTool] | None = None,
    workflows_by_name: dict | None = None,
    return_to_orchestrator_tool: BaseTool | None = None,
    tracing_context: LlmTracingContext | None = None,
    rag: RAGRetriever | None = None,
    trace: Any = None,
    turn_evidence: TurnEvidence | None = None,
) -> AgentTurnResult:
    delegate_tools = delegate_tools or []
    delegates_by_name = delegates_by_name or {}
    workflow_tools = workflow_tools or []
    workflows_by_name = workflows_by_name or {}
    knowledge_bases = knowledge_bases or []

    if langgraph_tools is None:
        langgraph_tools = build_executor_langgraph_tools(
            tools,
            connectors_by_id=connectors_by_id,
            search_knowledge_tool=search_knowledge_tool,
        )
        langgraph_tools.extend(delegate_tools)
        langgraph_tools.extend(workflow_tools)
        if return_to_orchestrator_tool is not None:
            langgraph_tools.append(return_to_orchestrator_tool)

    if not langgraph_tools:
        reply = await _simple_chat(
            orchestrator=orchestrator,
            system_prompt=system_prompt,
            history=history,
            tracing_context=tracing_context,
        )
        return AgentTurnResult(replies=[reply])

    router = ToolRouterContext(
        delegates_by_name=delegates_by_name,
        workflows_by_name=workflows_by_name,
        knowledge_bases=knowledge_bases,
        organization_id=organization_id,
        rag=rag,
        trace=trace,
        turn_evidence=turn_evidence,
        handle_return_to_orchestrator=return_to_orchestrator_tool is not None,
    )
    agent = create_bot_agent(
        orchestrator=orchestrator,
        tools=langgraph_tools,
        system_prompt=system_prompt,
        router=router,
        tracing_context=tracing_context,
    )

    messages = _history_to_messages(history)
    run_config = build_llm_run_config(tracing_context)
    try:
        if run_config:
            result = await agent.ainvoke({"messages": messages}, config=run_config)
        else:
            result = await agent.ainvoke({"messages": messages})
    except Exception as exc:
        if _is_pii_detection_error(exc):
            return AgentTurnResult(replies=[PII_BLOCKED_USER_MESSAGE])
        raise

    messages = result.get("messages", [])
    if router.delegation is not None:
        return AgentTurnResult(replies=[], delegation=router.delegation)
    if router.workflow_enter is not None:
        return AgentTurnResult(replies=[], workflow_enter=router.workflow_enter)
    if router.orchestrator_return:
        # Preserve any user-facing text on the same turn as return_to_orchestrator.
        reply = _extract_final_reply(messages, allow_tool_call_text=True)
        return AgentTurnResult(
            replies=[reply] if reply else [],
            orchestrator_return=True,
        )

    reply = _extract_final_reply(messages)
    if not reply:
        return AgentTurnResult(replies=[FALLBACK_REPLY])
    return AgentTurnResult(replies=[reply])


def _history_to_messages(history: list[dict[str, Any]]) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    for turn in history:
        role = turn.get("role")
        content = str(turn.get("content", ""))
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _content_to_text(content: Any) -> str:
    """Normalize Bedrock/Nova message content into plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                text = block.strip()
                if text:
                    parts.append(text)
                continue
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type in {"text", "output_text"}:
                text = str(block.get("text") or "").strip()
                if text:
                    parts.append(text)
            elif block_type == "reasoning_content":
                # Prefer final answer text; ignore model thinking blocks.
                continue
            else:
                text = str(block.get("text") or "").strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()


def _extract_final_reply(
    messages: list[Any],
    *,
    allow_tool_call_text: bool = False,
) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        if message.tool_calls and not allow_tool_call_text:
            continue
        text = _content_to_text(message.content)
        if text:
            return text
    return ""


def _is_pii_detection_error(exc: BaseException) -> bool:
    from langchain.agents.middleware import PIIDetectionError

    if isinstance(exc, PIIDetectionError):
        return True
    cause = exc.__cause__
    return isinstance(cause, PIIDetectionError)


async def _simple_chat(
    *,
    orchestrator: RuntimeOrchestrator,
    system_prompt: str,
    history: list[dict[str, Any]],
    tracing_context: LlmTracingContext | None = None,
) -> str:
    llm_config = orchestrator.llm_config
    llm = BedrockLLM(
        model_id=llm_config.model_id if llm_config else None,
        region=llm_config.region if llm_config else None,
        temperature=orchestrator.temperature,
        max_output_tokens=orchestrator.max_output_tokens,
        tracing_context=tracing_context,
    )
    return await llm.chat_from_history(system_prompt=system_prompt, history=history)
