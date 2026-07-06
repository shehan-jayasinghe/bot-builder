import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langchain.agents.middleware import PIIDetectionError

from app.domain.graph.langchain.orchestrator_agent import run_tool_agent_turn
from app.domain.graph.langchain.pii_middleware import PII_BLOCKED_USER_MESSAGE
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import RuntimeOrchestrator


def test_run_tool_agent_turn_returns_friendly_message_on_pii_block() -> None:
    orchestrator = RuntimeOrchestrator(id="a1", name="Bot", system_prompt="Help")

    async def _run() -> None:
        mock_agent = MagicMock()
        mock_agent.ainvoke = AsyncMock(side_effect=PIIDetectionError("api_key", []))

        with patch(
            "app.domain.graph.langchain.orchestrator_agent.create_bot_agent",
            return_value=mock_agent,
        ):
            result = await run_tool_agent_turn(
                orchestrator=orchestrator,
                system_prompt="Help",
                history=[{"role": "user", "content": "my key is sk-abcdefghijklmnopqrstuvwxyz123456"}],
                tools=[],
                connectors_by_id={},
                langgraph_tools=[MagicMock(name="tool")],
            )

        assert isinstance(result, AgentTurnResult)
        assert result.replies == [PII_BLOCKED_USER_MESSAGE]

    asyncio.run(_run())
