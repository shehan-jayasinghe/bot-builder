import asyncio
from unittest.mock import AsyncMock

from bson import ObjectId

from app.domain.constants.workflow_constants import (
    DEFAULT_STARTER_EDGES,
    DEFAULT_STARTER_NODES,
    WORKFLOW_STATUS_PUBLISHED,
)
from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.graph.search_knowledge_delegate import SEARCH_KNOWLEDGE_TOOL_NAME
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeKnowledgeBase,
    RuntimeOrchestrator,
    RuntimeWorkflow,
)
from app.domain.pipeline.rag.rag_result import RagRetrieveResult
from app.schemas.chat import ChatRequest
from app.services.chat_completion_service import ChatCompletionService

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")


def test_chat_completion_does_not_auto_retrieve_rag_with_kbs() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()
        rag = AsyncMock()

        agent_repository.find_by_id_for_organization.return_value = {
            "_id": AGENT_ID,
            "organization_id": ORG_ID,
            "name": "Bot",
            "system_prompt": "Help users.",
        }
        from app.domain.models.tracker import Tracker

        tracker = Tracker(sender_id="preview-1", assistant_id=str(AGENT_ID))
        tracker_service.load_or_create.return_value = tracker

        workflow = RuntimeWorkflow(
            id="6a3f9012d8139334274fbc00",
            name="hello",
            nodes=list(DEFAULT_STARTER_NODES),
            edges=list(DEFAULT_STARTER_EDGES),
            status=WORKFLOW_STATUS_PUBLISHED,
        )
        kb = RuntimeKnowledgeBase(
            id="6a3f9012d8139334274fbc01",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                knowledge_bases=[kb],
                workflows=[workflow],
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}
        from app.domain.graph.turn_result import AgentTurnResult

        orchestrator.run_turn.return_value = AgentTurnResult(replies=["Hello"])

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
            rag=rag,
        )

        response = await service.complete_preview(
            agent_id=str(AGENT_ID),
            organization_id=ORG_ID,
            request=ChatRequest(sender_id="preview-1", message="Hi"),
        )

        rag.retrieve.assert_not_awaited()
        assert response.messages[0].text == "Hello"

    asyncio.run(_run())


def test_orchestrator_search_knowledge_tool_invokes_retriever() -> None:
    async def _run() -> None:
        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        rag = AsyncMock()
        rag.retrieve.return_value = RagRetrieveResult(
            context="### FAQ\n- refund within 30 days",
            kb_ids=["kb-1"],
            chunk_count=1,
            storage_types=["vector"],
        )
        trace_events: list[tuple[str, dict]] = []

        async def trace(event: str, data: dict) -> None:
            trace_events.append((event, data))

        runner = OrchestratorRunner()
        orchestrator = RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            knowledge_bases=[kb],
        )

        result_text = await runner._run_search_knowledge_tool(
            tool_args={"query": "refund policy"},
            knowledge_bases=[kb],
            organization_id=ORG_ID,
            rag=rag,
            trace=trace,
        )

        assert "refund within 30 days" in result_text
        rag.retrieve.assert_awaited_once()
        assert ("tool_start", {"tool_name": SEARCH_KNOWLEDGE_TOOL_NAME, "arguments": {"query": "refund policy"}}) in trace_events
        tool_complete = next(data for event, data in trace_events if event == "tool_complete")
        assert tool_complete["tool_name"] == SEARCH_KNOWLEDGE_TOOL_NAME
        assert tool_complete["chunk_count"] == 1
        assert tool_complete["kb_ids"] == ["kb-1"]

    asyncio.run(_run())


def test_execute_tool_turn_search_knowledge_via_mocked_llm() -> None:
    async def _run() -> None:
        from unittest.mock import MagicMock, patch

        from langchain_core.messages import AIMessage

        from app.domain.graph.langchain.tool_router import run_search_knowledge_tool

        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        rag = AsyncMock()
        rag.retrieve.return_value = RagRetrieveResult(
            context="### FAQ\n- returns accepted within 30 days",
            kb_ids=["kb-1"],
            chunk_count=1,
        )
        search_tool = __import__(
            "app.domain.graph.search_knowledge_delegate",
            fromlist=["build_search_knowledge_tool"],
        ).build_search_knowledge_tool([kb], capability_catalog=None)

        runner = OrchestratorRunner()
        orchestrator = RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            knowledge_bases=[kb],
        )

        mock_agent = MagicMock()

        async def _fake_ainvoke(_input_state: dict, config: dict | None = None) -> dict:
            await run_search_knowledge_tool(
                tool_args={"query": "refund policy"},
                knowledge_bases=[kb],
                organization_id=ORG_ID,
                rag=rag,
                trace=None,
            )
            return {"messages": [AIMessage(content="Refunds are accepted within 30 days.")]}

        mock_agent.ainvoke = _fake_ainvoke

        with patch(
            "app.domain.graph.langchain.orchestrator_agent.create_bot_agent",
            return_value=mock_agent,
        ):
            result = await runner.execute_tool_turn(
                orchestrator=orchestrator,
                system_prompt="You are helpful.",
                history=[],
                tools=[],
                search_knowledge_tool=search_tool,
                knowledge_bases=[kb],
                organization_id=ORG_ID,
                connectors_by_id={},
                rag=rag,
            )

        assert result.replies == ["Refunds are accepted within 30 days."]
        rag.retrieve.assert_awaited_once()

    asyncio.run(_run())


def test_execute_tool_turn_skips_executor_named_search_knowledge() -> None:
    async def _run() -> None:
        from unittest.mock import MagicMock, patch

        from langchain_core.messages import AIMessage

        from app.domain.graph.langchain.tool_router import run_search_knowledge_tool
        from app.domain.models.runtime_bundle import RuntimeTool

        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="FAQ",
            storage_type="vector",
            status="active",
        )
        rag = AsyncMock()
        rag.retrieve.return_value = RagRetrieveResult(context="KB hit", kb_ids=["kb-1"], chunk_count=1)
        search_tool = __import__(
            "app.domain.graph.search_knowledge_delegate",
            fromlist=["build_search_knowledge_tool"],
        ).build_search_knowledge_tool([kb], capability_catalog=None)
        executor_tool = RuntimeTool(
            id="tool-1",
            name=SEARCH_KNOWLEDGE_TOOL_NAME,
            description="Should not run as executor",
            executor="http",
            connector_id="conn-1",
            status="active",
        )

        runner = OrchestratorRunner()
        orchestrator = RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            knowledge_bases=[kb],
            tools=[executor_tool],
        )

        mock_agent = MagicMock()

        async def _fake_ainvoke(_input_state: dict, config: dict | None = None) -> dict:
            await run_search_knowledge_tool(
                tool_args={"query": "policy"},
                knowledge_bases=[kb],
                organization_id=ORG_ID,
                rag=rag,
                trace=None,
            )
            return {"messages": [AIMessage(content="Done")]}

        mock_agent.ainvoke = _fake_ainvoke

        with patch(
            "app.domain.graph.langchain.orchestrator_agent.create_bot_agent",
            return_value=mock_agent,
        ):
            await runner.execute_tool_turn(
                orchestrator=orchestrator,
                system_prompt="You are helpful.",
                history=[],
                tools=[executor_tool],
                search_knowledge_tool=search_tool,
                knowledge_bases=[kb],
                organization_id=ORG_ID,
                connectors_by_id={"conn-1": {"base_url": "https://example.com"}},
                rag=rag,
            )

        rag.retrieve.assert_awaited_once()

    asyncio.run(_run())
