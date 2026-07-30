import asyncio
from unittest.mock import AsyncMock, MagicMock

from bson import ObjectId

from app.domain.constants.workflow_constants import (
    DEFAULT_STARTER_EDGES,
    DEFAULT_STARTER_NODES,
    WORKFLOW_STATUS_PUBLISHED,
)
from app.domain.graph.chat_graph import ChatGraph
from app.domain.graph.turn_result import AgentTurnResult, WorkflowEnterRequest
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeOrchestrator,
    RuntimeWorkflow,
)
from app.domain.models.tracker import Tracker
from app.domain.workflow.slot_validator import validate_slot_value
from app.domain.workflow.workflow_delegate import (
    build_workflow_delegate_tools,
    normalize_workflow_name,
    workflow_tool_name,
)
from app.domain.workflow.workflow_graph_runner import WorkflowGraphRunner, WorkflowReply
from app.schemas.chat import ChatRequest
from app.services.chat_completion_service import ChatCompletionService

ORG_ID = "6a3b7c61d8139334274fbbfc"
AGENT_ID = ObjectId("6a3b7c61d8139334274fbbf1")
WORKFLOW_ID = "6a3f9012d8139334274fbc00"


def _hello_workflow() -> RuntimeWorkflow:
    return RuntimeWorkflow(
        id=WORKFLOW_ID,
        name="hello",
        nodes=list(DEFAULT_STARTER_NODES),
        edges=list(DEFAULT_STARTER_EDGES),
        status=WORKFLOW_STATUS_PUBLISHED,
    )


def test_normalize_workflow_name() -> None:
    assert normalize_workflow_name("Hello Flow") == "hello_flow"
    assert workflow_tool_name("hello") == "workflow_hello"


def test_validate_slot_value_pattern() -> None:
    ok, _ = validate_slot_value(
        "123456",
        validation={"type": "string", "pattern": r"^[0-9]{6,12}$"},
    )
    assert ok is True

    bad, _ = validate_slot_value(
        "abc",
        validation={"type": "string", "pattern": r"^[0-9]{6,12}$"},
    )
    assert bad is False


def test_workflow_graph_runner_message_substitution() -> None:
    workflow = RuntimeWorkflow(
        id=WORKFLOW_ID,
        name="greet",
        nodes=[
            {"id": "start-1", "type": "start", "data": {}},
            {
                "id": "message-1",
                "type": "message",
                "data": {"text": "Hello {{customer_name}}"},
            },
        ],
        edges=[{"id": "edge-1", "source": "start-1", "target": "message-1"}],
        status=WORKFLOW_STATUS_PUBLISHED,
    )
    runner = WorkflowGraphRunner()
    state = runner.build_initial_state(workflow)
    assert state is not None
    state["slots"] = {"customer_name": "Sam"}

    result = asyncio.run(
        runner.run_turn(
            workflow=workflow,
            state=state,
            user_message="ignored",
        ),
    )

    assert result.replies[0].text == "Hello Sam"
    assert result.exited is True


def test_workflow_graph_runner_input_prompt_then_capture() -> None:
    workflow = RuntimeWorkflow(
        id=WORKFLOW_ID,
        name="capture",
        nodes=[
            {"id": "start-1", "type": "start", "data": {}},
            {
                "id": "input-1",
                "type": "input",
                "data": {
                    "slot_name": "customer_id",
                    "prompt": "Enter your customer ID.",
                    "retry_message": "Invalid ID.",
                    "validation": {"type": "string", "pattern": r"^[0-9]{6}$"},
                },
            },
            {
                "id": "message-1",
                "type": "message",
                "data": {"text": "Thanks {{customer_id}}"},
            },
        ],
        edges=[
            {"id": "edge-1", "source": "start-1", "target": "input-1"},
            {"id": "edge-2", "source": "input-1", "target": "message-1"},
        ],
        status=WORKFLOW_STATUS_PUBLISHED,
    )
    runner = WorkflowGraphRunner()
    state = runner.build_initial_state(workflow)
    assert state is not None

    first = asyncio.run(
        runner.run_turn(workflow=workflow, state=state, user_message="hello"),
    )
    assert first.replies[0].text == "Enter your customer ID."
    assert state["awaiting_slot"] == "customer_id"
    assert first.exited is False

    second = asyncio.run(
        runner.run_turn(workflow=workflow, state=state, user_message="abc"),
    )
    assert second.replies[0].text == "Invalid ID."
    assert state["slots"] == {}

    third = asyncio.run(
        runner.run_turn(workflow=workflow, state=state, user_message="123456"),
    )
    assert third.replies[0].text == "Thanks 123456"
    assert third.exited is True


def test_workflow_graph_runner_end_clears_via_chat_graph() -> None:
    workflow = RuntimeWorkflow(
        id=WORKFLOW_ID,
        name="farewell",
        nodes=[
            {"id": "start-1", "type": "start", "data": {}},
            {"id": "end-1", "type": "end", "data": {"text": "Goodbye"}},
        ],
        edges=[{"id": "edge-1", "source": "start-1", "target": "end-1"}],
        status=WORKFLOW_STATUS_PUBLISHED,
    )
    tracker = Tracker(sender_id="user-1", assistant_id=str(AGENT_ID))
    tracker.enter_workflow(
        state={
            "workflow_id": WORKFLOW_ID,
            "current_node_id": "end-1",
            "slots": {},
            "awaiting_slot": None,
        },
    )
    graph = ChatGraph()

    result = asyncio.run(
        graph.run_turn(
            bundle=RuntimeBundle(
                organization_id=ORG_ID,
                orchestrator=RuntimeOrchestrator(
                    id=str(AGENT_ID),
                    name="Bot",
                    system_prompt="Help users.",
                    workflows=[workflow],
                ),
            ),
            tracker=tracker,
            user_message="bye",
            system_prompt="Help users.",
            connectors_by_id={},
        ),
    )

    assert result.replies[0].text == "Goodbye"
    assert tracker.active_flow_state is None
    assert tracker.active_agent_kind == "orchestrator"
    assert result.routing.get("workflow_exited") is True


def test_build_workflow_delegate_tools_includes_routing_hint() -> None:
    workflow = _hello_workflow()
    from app.domain.models.capability_catalog import CapabilityCatalog, CapabilityEntry

    catalog = CapabilityCatalog(
        workflows={WORKFLOW_ID: CapabilityEntry(routing_hint="Greet new users")},
    )
    tools, by_name = build_workflow_delegate_tools(
        [workflow],
        reserved_names=set(),
        capability_catalog=catalog,
    )

    assert len(tools) == 1
    assert "Greet new users" in tools[0].description
    assert workflow_tool_name("hello") in by_name


def test_chat_graph_first_message_invokes_orchestrator_not_auto_start() -> None:
    workflow = _hello_workflow()
    bundle = RuntimeBundle(
        organization_id=ORG_ID,
        orchestrator=RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            workflows=[workflow],
        ),
    )
    tracker = Tracker(sender_id="preview-1", assistant_id=str(AGENT_ID))
    tracker.append_user_message(message="hello", metadata={})
    orchestrator = AsyncMock()
    orchestrator.run_turn.return_value = AgentTurnResult(replies=["How can I help?"])
    graph = ChatGraph(orchestrator=orchestrator)

    result = asyncio.run(
        graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="hello",
            system_prompt="Help users.",
            connectors_by_id={},
        ),
    )

    orchestrator.run_turn.assert_awaited_once()
    assert result.replies[0].text == "How can I help?"
    assert tracker.active_flow_state is None
    assert result.routing.get("mode") == "orchestrator"


def test_chat_completion_preview_loads_bundle_for_preview() -> None:
    async def _run() -> None:
        agent_repository = AsyncMock()
        tracker_service = AsyncMock()
        runtime_bundle_loader = AsyncMock()
        orchestrator = AsyncMock()
        chat_graph = AsyncMock()

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
                workflows=[_hello_workflow()],
            ),
            organization_id=ORG_ID,
        )
        runtime_bundle_loader.load.return_value = bundle
        runtime_bundle_loader.load_connectors_for_tools.return_value = {}

        from app.domain.workflow.workflow_graph_runner import WorkflowReply

        chat_graph.run_turn.return_value = MagicMock(
            replies=[WorkflowReply(text="Welcome")],
            routing={
                "mode": "orchestrator",
                "type": "workflow",
                "workflow_exited": True,
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
            request=ChatRequest(sender_id="preview-1", message="hello"),
        )

        runtime_bundle_loader.load.assert_awaited_once_with(
            agent_doc=agent_repository.find_by_id_for_organization.return_value,
            for_preview=True,
        )
        chat_graph.run_turn.assert_awaited_once()
        assert response.messages[0].text == "Welcome"

    asyncio.run(_run())


def test_orchestrator_workflow_tool_enters_workflow() -> None:
    workflow = _hello_workflow()
    bundle = RuntimeBundle(
        organization_id=ORG_ID,
        orchestrator=RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            workflows=[workflow],
        ),
    )
    tracker = Tracker(sender_id="preview-1", assistant_id=str(AGENT_ID))
    tracker.append_user_message(message="start hello flow", metadata={})
    tracker.append_user_message(message="again", metadata={})

    orchestrator = AsyncMock()
    orchestrator.run_turn.return_value = AgentTurnResult(
        replies=[],
        workflow_enter=WorkflowEnterRequest(
            workflow=workflow,
            function_name="workflow_hello",
            args={},
        ),
    )
    graph = ChatGraph(orchestrator=orchestrator)

    result = asyncio.run(
        graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="start hello flow",
            system_prompt="Help users.",
            connectors_by_id={},
        ),
    )

    orchestrator.run_turn.assert_awaited_once()
    assert result.replies[0].text == "Welcome"
    assert result.routing.get("enter_reason") == "orchestrator_tool"


def test_workflow_takes_priority_over_sticky_sub_agent() -> None:
    workflow = _hello_workflow()
    bundle = RuntimeBundle(
        organization_id=ORG_ID,
        orchestrator=RuntimeOrchestrator(
            id=str(AGENT_ID),
            name="Bot",
            system_prompt="Help users.",
            workflows=[workflow],
        ),
    )
    tracker = Tracker(
        sender_id="preview-1",
        assistant_id=str(AGENT_ID),
        active_agent_id="6a3f9012d8139334274fbc04",
        active_agent_kind="sub_agent",
        active_flow_state={
            "workflow_id": WORKFLOW_ID,
            "current_node_id": "message-1",
            "slots": {},
            "awaiting_slot": None,
        },
    )
    tracker.append_user_message(message="hi", metadata={})

    orchestrator = AsyncMock()
    orchestrator.run_turn = AsyncMock()
    graph = ChatGraph(orchestrator=orchestrator)

    result = asyncio.run(
        graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message="next",
            system_prompt="Help users.",
            connectors_by_id={},
        ),
    )

    orchestrator.run_turn.assert_not_awaited()
    assert result.routing.get("mode") == "workflow"
    assert result.replies[0].text == "Welcome"
