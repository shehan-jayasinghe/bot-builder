from typing import Any

from app.domain.constants.chat_constants import MAX_HISTORY_TURNS
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeTool
from app.domain.models.tracker import Tracker
from app.domain.executors.langgraph_tools import build_langgraph_tools
from app.infrastructure.ai.llm import BedrockLLM

MAX_TOOL_ITERATIONS = 5


class OrchestratorRunner:
    """Runs orchestrator LLM turns with optional tool calling."""

    async def run_turn(
        self,
        *,
        bundle: RuntimeBundle,
        tracker: Tracker,
        user_message: str,
        rag_context: str,
        connectors_by_id: dict[str, dict[str, Any]],
    ) -> list[str]:
        orchestrator = bundle.orchestrator
        system_prompt = self._build_system_prompt(orchestrator, rag_context=rag_context)
        history = _cap_history(tracker.get_history())

        if not orchestrator.tools:
            reply = await self._simple_chat(
                orchestrator=orchestrator,
                system_prompt=system_prompt,
                history=history,
            )
            return [reply]

        return await self._chat_with_tools(
            orchestrator=orchestrator,
            system_prompt=system_prompt,
            history=history,
            tools=orchestrator.tools,
            connectors_by_id=connectors_by_id,
        )

    @staticmethod
    def _build_system_prompt(
        orchestrator: RuntimeOrchestrator,
        *,
        rag_context: str,
    ) -> str:
        return orchestrator.build_system_prompt(rag_context=rag_context or None)

    @staticmethod
    def _build_llm(orchestrator: RuntimeOrchestrator) -> BedrockLLM:
        llm_config = orchestrator.llm_config
        return BedrockLLM(
            model_id=llm_config.model_id if llm_config else None,
            region=llm_config.region if llm_config else None,
            temperature=orchestrator.temperature,
            max_output_tokens=orchestrator.max_output_tokens,
        )

    async def _simple_chat(
        self,
        *,
        orchestrator: RuntimeOrchestrator,
        system_prompt: str,
        history: list[dict[str, Any]],
    ) -> str:
        llm = self._build_llm(orchestrator)
        return await llm.chat_from_history(system_prompt=system_prompt, history=history)

    async def _chat_with_tools(
        self,
        *,
        orchestrator: RuntimeOrchestrator,
        system_prompt: str,
        history: list[dict[str, Any]],
        tools: list[RuntimeTool],
        connectors_by_id: dict[str, dict[str, Any]],
    ) -> list[str]:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

        pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for tool in tools:
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

        if not pairs:
            reply = await self._simple_chat(
                orchestrator=orchestrator,
                system_prompt=system_prompt,
                history=history,
            )
            return [reply]

        langgraph_tools = build_langgraph_tools(pairs)
        tools_by_name = {tool.name: tool for tool in langgraph_tools}
        llm = self._build_llm(orchestrator).get_client().bind_tools(langgraph_tools)

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
            response = await llm.ainvoke(messages)
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                return [str(response.content)]

            messages.append(response)
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                if not tool_name or tool_name not in tools_by_name:
                    tool_result = f"Unknown tool: {tool_name}"
                else:
                    tool_result = await tools_by_name[tool_name].ainvoke(
                        tool_call.get("args") or {},
                    )
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=str(tool_call.get("id") or tool_name),
                    ),
                )

        return ["I couldn't complete that request. Please try again."]


def _cap_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(history) <= MAX_HISTORY_TURNS:
        return list(history)
    return list(history[-MAX_HISTORY_TURNS:])
