import asyncio
from unittest.mock import AsyncMock, MagicMock

from bson import ObjectId

from app.domain.graph.sub_agent_delegate import (
    build_delegate_langgraph_tools,
    build_sub_agent_system_prompt,
    normalize_sub_agent_name,
)
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeKnowledgeBase,
    RuntimeOrchestrator,
    RuntimeSubAgent,
    RuntimeSubAgentParameter,
    RuntimeTool,
)
from app.domain.models.tracker import Tracker
from app.schemas.chat import ChatRequest
from app.services.chat_completion_service import ChatCompletionService

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")
SUB_AGENT_ID = "6a3f9012d8139334274fbc04"


def test_normalize_sub_agent_name() -> None:
    assert normalize_sub_agent_name("Research Agent") == "research_agent"


def test_build_delegate_tools_skips_tool_name_collisions() -> None:
    sub_agents = [
        RuntimeSubAgent(
            id=SUB_AGENT_ID,
            name="research_agent",
            instructions="Research only.",
            status="active",
        ),
        RuntimeSubAgent(
            id="6a3f9012d8139334274fbc05",
            name="send_payment",
            instructions="Payments only.",
            status="active",
        ),
    ]

    tools, by_name = build_delegate_langgraph_tools(
        sub_agents,
        reserved_names={"send_payment"},
    )

    assert len(tools) == 1
    assert "research_agent" in by_name
    assert "send_payment" not in by_name


def test_runtime_orchestrator_find_sub_agent_by_name() -> None:
    orchestrator = RuntimeOrchestrator(
        id=str(AGENT_ID),
        name="Bot",
        system_prompt="Help users.",
        sub_agents=[
            RuntimeSubAgent(
                id=SUB_AGENT_ID,
                name="research_agent",
                instructions="Research only.",
                status="active",
            ),
        ],
    )

    found = orchestrator.find_sub_agent_by_name("research_agent")
    assert found is not None
    assert found.id == SUB_AGENT_ID
    assert orchestrator.find_sub_agent_by_name("missing") is None


def test_build_sub_agent_system_prompt_includes_delegate_args() -> None:
    sub_agent = RuntimeSubAgent(
        id=SUB_AGENT_ID,
        name="research_agent",
        instructions="You research things.",
        parameters=[
            RuntimeSubAgentParameter(name="query", type="string", description="Question", required=True),
        ],
        status="active",
    )

    prompt = build_sub_agent_system_prompt(
        sub_agent,
        delegate_args={"query": "loyalty rules"},
    )

    assert "You research things." in prompt
    assert "loyalty rules" in prompt
    assert "Retrieved context" not in prompt


def test_runtime_bundle_all_runtime_tools_includes_sub_agent_tools() -> None:
    bundle = RuntimeBundle(
        organization_id=ORG_ID,
        orchestrator=RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            tools=[
                RuntimeTool(
                    id="tool-1",
                    name="parent_tool",
                    description="Parent",
                    executor="http",
                    connector_id="conn-1",
                    status="active",
                ),
            ],
            sub_agents=[
                RuntimeSubAgent(
                    id=SUB_AGENT_ID,
                    name="research_agent",
                    instructions="Research only.",
                    tools=[
                        RuntimeTool(
                            id="tool-2",
                            name="sub_tool",
                            description="Sub",
                            executor="http",
                            connector_id="conn-2",
                            status="active",
                        ),
                    ],
                    status="active",
                ),
            ],
        ),
    )

    names = {tool.name for tool in bundle.all_runtime_tools()}
    assert names == {"parent_tool", "sub_tool"}


def test_chat_completion_persists_delegate_routing() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()

        agent_repository.find_by_id_for_organization.return_value = {
            "_id": AGENT_ID,
            "organization_id": ORG_ID,
            "name": "Bot",
            "system_prompt": "Help users.",
        }
        tracker = Tracker(sender_id="preview-1", assistant_id=str(AGENT_ID))
        tracker_service.load_or_create.return_value = tracker

        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                sub_agents=[
                    RuntimeSubAgent(
                        id=SUB_AGENT_ID,
                        name="research_agent",
                        instructions="Research only.",
                        status="active",
                    ),
                ],
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}
        orchestrator.run_turn.return_value = AgentTurnResult(
            replies=["Scoped research answer"],
            routing={
                "mode": "delegate",
                "type": "delegate",
                "sub_agent_id": SUB_AGENT_ID,
                "sub_agent_name": "research_agent",
                "args": {"query": "loyalty rules"},
            },
        )

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
        )

        response = await service.complete_preview(
            agent_id=str(AGENT_ID),
            organization_id=ORG_ID,
            request=ChatRequest(sender_id="preview-1", message="Find loyalty rules"),
        )

        assert response.messages[0].text == "Scoped research answer"
        assert tracker.active_agent_kind == "sub_agent"
        assert tracker.active_agent_id == SUB_AGENT_ID
        assert tracker.last_routing_decision is not None
        assert tracker.last_routing_decision["mode"] == "delegate"
        runtime_bundle_loader.load_connectors_for_tools.assert_awaited_once()
        connector_tools = runtime_bundle_loader.load_connectors_for_tools.await_args.kwargs["tools"]
        assert connector_tools == bundle.all_runtime_tools()

    asyncio.run(_run())


def test_runtime_orchestrator_find_sub_agent_by_id() -> None:
    orchestrator = RuntimeOrchestrator(
        id=str(AGENT_ID),
        name="Bot",
        system_prompt="Help users.",
        sub_agents=[
            RuntimeSubAgent(
                id=SUB_AGENT_ID,
                name="research_agent",
                instructions="Research only.",
                status="active",
            ),
        ],
    )

    found = orchestrator.find_sub_agent_by_id(SUB_AGENT_ID)
    assert found is not None
    assert found.name == "research_agent"
    assert orchestrator.find_sub_agent_by_id("missing") is None


def test_chat_completion_sticky_sub_agent_on_follow_up_turn() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()

        agent_repository.find_by_id_for_organization.return_value = {
            "_id": AGENT_ID,
            "organization_id": ORG_ID,
            "name": "Bot",
            "system_prompt": "Help users.",
        }
        tracker = Tracker(
            sender_id="preview-1",
            assistant_id=str(AGENT_ID),
            active_agent_id=SUB_AGENT_ID,
            active_agent_kind="sub_agent",
            last_routing_decision={
                "mode": "delegate",
                "sub_agent_id": SUB_AGENT_ID,
                "sub_agent_name": "research_agent",
                "args": {"query": "loyalty rules"},
            },
        )
        tracker_service.load_or_create.return_value = tracker

        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                sub_agents=[
                    RuntimeSubAgent(
                        id=SUB_AGENT_ID,
                        name="research_agent",
                        instructions="Research only.",
                        status="active",
                    ),
                ],
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}

        chat_graph = AsyncMock()
        chat_graph.run_turn.return_value = MagicMock(
            replies=[MagicMock(text="Sticky follow-up answer", buttons=None)],
            routing={
                "mode": "delegate",
                "type": "delegate",
                "sub_agent_id": SUB_AGENT_ID,
                "sub_agent_name": "research_agent",
                "args": {"query": "loyalty rules"},
                "sticky": True,
            },
        )

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
            chat_graph=chat_graph,
        )

        response = await service.complete_preview(
            agent_id=str(AGENT_ID),
            organization_id=ORG_ID,
            request=ChatRequest(sender_id="preview-1", message="Follow up"),
        )

        assert response.messages[0].text == "Sticky follow-up answer"
        assert tracker.active_agent_kind == "sub_agent"
        assert tracker.active_agent_id == SUB_AGENT_ID
        orchestrator.run_turn.assert_not_awaited()
        chat_graph.run_turn.assert_awaited_once()

    asyncio.run(_run())


def test_chat_graph_sticky_sub_agent_skips_orchestrator() -> None:
    async def _run() -> None:
        from app.domain.graph.chat_graph import ChatGraph

        sub_agent = RuntimeSubAgent(
            id=SUB_AGENT_ID,
            name="research_agent",
            instructions="Research only.",
            status="active",
        )
        bundle = RuntimeBundle(
            organization_id=ORG_ID,
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                sub_agents=[sub_agent],
            ),
        )
        tracker = Tracker(
            sender_id="user-1",
            assistant_id=str(AGENT_ID),
            active_agent_id=SUB_AGENT_ID,
            active_agent_kind="sub_agent",
            last_routing_decision={
                "mode": "delegate",
                "sub_agent_id": SUB_AGENT_ID,
                "args": {"query": "rules"},
            },
        )

        orchestrator = AsyncMock()
        orchestrator.run_turn = AsyncMock()
        orchestrator.execute_tool_turn = AsyncMock(
            return_value=AgentTurnResult(replies=["Sticky answer"]),
        )

        graph = ChatGraph(orchestrator=orchestrator)
        result = await graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="Tell me more",
            system_prompt="Orchestrator prompt",
            connectors_by_id={},
        )

        orchestrator.run_turn.assert_not_awaited()
        orchestrator.execute_tool_turn.assert_awaited_once()
        assert result.routing["mode"] == "delegate"
        assert result.routing["sticky"] is True
        assert result.routing["sub_agent_id"] == SUB_AGENT_ID
        assert result.replies[0].text == "Sticky answer"

    asyncio.run(_run())


def test_chat_graph_sticky_falls_back_when_sub_agent_missing() -> None:
    async def _run() -> None:
        from app.domain.graph.chat_graph import ChatGraph

        bundle = RuntimeBundle(
            organization_id=ORG_ID,
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
            ),
        )
        tracker = Tracker(
            sender_id="user-1",
            assistant_id=str(AGENT_ID),
            active_agent_id=SUB_AGENT_ID,
            active_agent_kind="sub_agent",
        )

        orchestrator = AsyncMock()
        orchestrator.run_turn = AsyncMock(
            return_value=AgentTurnResult(replies=["Orchestrator answer"]),
        )

        graph = ChatGraph(orchestrator=orchestrator)
        result = await graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="Hello",
            system_prompt="Orchestrator prompt",
            connectors_by_id={},
        )

        assert tracker.active_agent_kind == "orchestrator"
        orchestrator.run_turn.assert_awaited_once()
        assert result.replies[0].text == "Orchestrator answer"

    asyncio.run(_run())


def test_orchestrator_run_turn_handles_delegation_without_rag_prefetch() -> None:
    async def _run() -> None:
        from app.domain.graph.orchestrator import OrchestratorRunner
        from app.domain.graph.turn_result import DelegationRequest

        runner = OrchestratorRunner()
        sub_agent = RuntimeSubAgent(
            id=SUB_AGENT_ID,
            name="research_agent",
            instructions="Research only.",
            knowledge_bases=[
                RuntimeKnowledgeBase(
                    id="kb-1",
                    name="Research KB",
                    storage_type="vector",
                    status="active",
                ),
            ],
            status="active",
        )
        bundle = RuntimeBundle(
            organization_id=ORG_ID,
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                sub_agents=[sub_agent],
            ),
        )
        tracker = Tracker(sender_id="user-1", assistant_id=str(AGENT_ID))
        rag = AsyncMock()

        runner.execute_tool_turn = AsyncMock(  # type: ignore[method-assign]
            return_value=AgentTurnResult(
                replies=[],
                delegation=DelegationRequest(
                    sub_agent=sub_agent,
                    args={"query": "rules"},
                    function_name="research_agent",
                ),
            ),
        )

        sub_runner = MagicMock()
        sub_runner.run_turn = AsyncMock(
            return_value=AgentTurnResult(replies=["Delegated answer"]),
        )
        runner_module = __import__("app.domain.graph.orchestrator", fromlist=["SubAgentRunner"])
        original = runner_module.SubAgentRunner
        runner_module.SubAgentRunner = MagicMock(return_value=sub_runner)  # type: ignore[misc]

        try:
            result = await runner.run_turn(
                bundle=bundle,
                tracker=tracker,
                user_message="research loyalty",
                system_prompt="You are the orchestrator.",
                connectors_by_id={},
                rag=rag,
            )
        finally:
            runner_module.SubAgentRunner = original  # type: ignore[misc]

        assert result.replies == ["Delegated answer"]
        assert result.routing["mode"] == "delegate"
        assert result.routing["sub_agent_id"] == SUB_AGENT_ID
        rag.retrieve.assert_not_awaited()
        sub_runner.run_turn.assert_awaited_once()
        sub_call = sub_runner.run_turn.await_args.kwargs
        assert sub_call["bundle"] is bundle
        assert sub_call["rag"] is rag

    asyncio.run(_run())


def test_sub_agent_return_to_orchestrator_resets_sticky_state() -> None:
    async def _run() -> None:
        from app.domain.graph.chat_graph import ChatGraph

        sub_agent = RuntimeSubAgent(
            id=SUB_AGENT_ID,
            name="research_agent",
            instructions="Research only.",
            status="active",
        )
        bundle = RuntimeBundle(
            organization_id=ORG_ID,
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
                sub_agents=[sub_agent],
            ),
        )
        tracker = Tracker(
            sender_id="user-1",
            assistant_id=str(AGENT_ID),
            active_agent_id=SUB_AGENT_ID,
            active_agent_kind="sub_agent",
            last_routing_decision={"mode": "delegate", "sub_agent_id": SUB_AGENT_ID},
        )

        orchestrator = AsyncMock()
        orchestrator.run_turn = AsyncMock()
        orchestrator.execute_tool_turn = AsyncMock(
            return_value=AgentTurnResult(replies=[], orchestrator_return=True),
        )

        graph = ChatGraph(orchestrator=orchestrator)
        result = await graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="Go back",
            system_prompt="Orchestrator prompt",
            connectors_by_id={},
        )

        assert tracker.active_agent_kind == "orchestrator"
        assert tracker.active_agent_id == str(AGENT_ID)
        assert result.routing["mode"] == "orchestrator"
        orchestrator.run_turn.assert_not_awaited()

    asyncio.run(_run())


def test_sub_agent_runner_registers_search_knowledge_when_kbs_exist() -> None:
    async def _run() -> None:
        from app.domain.graph.sub_agent_delegate import SubAgentRunner

        kb = RuntimeKnowledgeBase(
            id="kb-1",
            name="Research KB",
            storage_type="vector",
            status="active",
        )
        sub_agent = RuntimeSubAgent(
            id=SUB_AGENT_ID,
            name="research_agent",
            instructions="Research only.",
            knowledge_bases=[kb],
            status="active",
        )
        bundle = RuntimeBundle(
            organization_id=ORG_ID,
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
            ),
        )
        tracker = Tracker(sender_id="user-1", assistant_id=str(AGENT_ID))
        tool_executor = AsyncMock()
        tool_executor.execute_tool_turn.return_value = AgentTurnResult(replies=["Answer"])

        runner = SubAgentRunner(tool_executor=tool_executor)
        await runner.run_turn(
            sub_agent=sub_agent,
            orchestrator=bundle.orchestrator,
            tracker=tracker,
            delegate_args={"query": "rules"},
            bundle=bundle,
            connectors_by_id={},
            rag=AsyncMock(),
        )

        call_kwargs = tool_executor.execute_tool_turn.await_args.kwargs
        assert call_kwargs["search_knowledge_tool"] is not None
        assert call_kwargs["search_knowledge_tool"].name == "search_knowledge"
        assert call_kwargs["knowledge_bases"] == [kb]
        assert call_kwargs["return_to_orchestrator_tool"] is not None
        assert call_kwargs["return_to_orchestrator_tool"].name == "return_to_orchestrator"

    asyncio.run(_run())
