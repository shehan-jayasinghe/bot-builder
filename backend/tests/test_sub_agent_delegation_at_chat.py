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
        rag_context="chunk-1",
    )

    assert "You research things." in prompt
    assert "loyalty rules" in prompt
    assert "chunk-1" in prompt


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


def test_chat_completion_resets_sub_agent_before_next_turn() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()

        agent_repository.find_by_id_for_organization.return_value = {
            "_id": AGENT_ID,
            "organization_id": ORG_ID,
        }
        tracker = Tracker(
            sender_id="preview-1",
            assistant_id=str(AGENT_ID),
            active_agent_id=SUB_AGENT_ID,
            active_agent_kind="sub_agent",
            last_routing_decision={"mode": "delegate", "sub_agent_id": SUB_AGENT_ID},
        )
        tracker_service.load_or_create.return_value = tracker

        bundle = RuntimeBundle(
            orchestrator=RuntimeOrchestrator(
                id=str(AGENT_ID),
                name="Bot",
                system_prompt="Help users.",
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}
        orchestrator.run_turn.return_value = AgentTurnResult(replies=["Back to orchestrator"])

        service = ChatCompletionService(
            assistant_loader=AsyncMock(),
            agent_repository=agent_repository,
            tracker_service=tracker_service,
            runtime_bundle_loader=runtime_bundle_loader,
            orchestrator=orchestrator,
        )

        await service.complete_preview(
            agent_id=str(AGENT_ID),
            organization_id=ORG_ID,
            request=ChatRequest(sender_id="preview-1", message="Follow up"),
        )

        assert tracker.active_agent_kind == "orchestrator"
        assert tracker.active_agent_id == str(AGENT_ID)

    asyncio.run(_run())


def test_orchestrator_run_turn_handles_delegation_with_mocked_sub_runner() -> None:
    async def _run() -> None:
        from app.domain.graph.orchestrator import OrchestratorRunner
        from app.domain.graph.turn_result import DelegationRequest

        runner = OrchestratorRunner()
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
        tracker = Tracker(sender_id="user-1", assistant_id=str(AGENT_ID))

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
        sub_runner.run_turn = AsyncMock(return_value=["Delegated answer"])
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
                rag=AsyncMock(),
            )
        finally:
            runner_module.SubAgentRunner = original  # type: ignore[misc]

        assert result.replies == ["Delegated answer"]
        assert result.routing["mode"] == "delegate"
        assert result.routing["sub_agent_id"] == SUB_AGENT_ID
        sub_runner.run_turn.assert_awaited_once()

    asyncio.run(_run())
