from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.domain.graph.chat_router_compiler import compile_chat_router_graph
from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.graph.sub_agent_delegate import SubAgentRunner
from app.domain.graph.turn_evidence import TurnEvidence
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeWorkflow
from app.domain.models.tracker import Tracker
from app.domain.workflow.workflow_graph_runner import (
    WorkflowGraphRunner,
    WorkflowReply,
    WorkflowTurnResult,
)
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext

if TYPE_CHECKING:
    from app.domain.pipeline.rag.retriever import RAGRetriever

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass
class ChatGraphResult:
    replies: list[WorkflowReply] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=lambda: {"mode": "orchestrator"})
    turn_evidence: dict[str, Any] | None = None


@dataclass
class _ChatTurnContext:
    bundle: RuntimeBundle
    tracker: Tracker
    user_message: str
    system_prompt: str
    connectors_by_id: dict[str, dict[str, Any]]
    tracing_context: LlmTracingContext | None
    rag: "RAGRetriever | None"
    trace: TraceCallback | None
    turn_evidence: TurnEvidence
    workflow_enter: RuntimeWorkflow | None = None
    workflow_enter_reason: str = "orchestrator_tool"


class ChatGraph:
    def __init__(
        self,
        *,
        orchestrator: OrchestratorRunner | None = None,
        workflow_graph_runner: WorkflowGraphRunner | None = None,
    ) -> None:
        self._orchestrator = orchestrator or OrchestratorRunner()
        self._workflow_graph_runner = workflow_graph_runner or WorkflowGraphRunner()
        self._turn: _ChatTurnContext | None = None
        self._compiled_router = compile_chat_router_graph(self)

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
    ) -> ChatGraphResult:
        turn_evidence = TurnEvidence(user_message=user_message)
        self._turn = _ChatTurnContext(
            bundle=bundle,
            tracker=tracker,
            user_message=user_message,
            system_prompt=system_prompt,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
            turn_evidence=turn_evidence,
        )
        try:
            final_state = await self._compiled_router.ainvoke(
                {
                    "finished": False,
                    "needs_workflow_enter": False,
                    "turn_evidence": turn_evidence.to_dict(),
                },
            )
            result = final_state.get("result")
            if isinstance(result, ChatGraphResult):
                return self._attach_turn_evidence(result)
            return self._attach_turn_evidence(ChatGraphResult())
        finally:
            self._turn = None

    def _attach_turn_evidence(self, result: ChatGraphResult) -> ChatGraphResult:
        turn = self._turn
        if turn is None:
            return result
        evidence = turn.turn_evidence
        evidence.set_assistant_replies([reply.text for reply in result.replies if reply.text])
        evidence.set_routing(result.routing)
        result.turn_evidence = evidence.to_dict()
        return result

    def route_session(self) -> str:
        turn = self._require_turn()
        flow_state = turn.tracker.active_flow_state
        if flow_state is not None:
            workflow = turn.bundle.find_workflow_by_id(str(flow_state.get("workflow_id", "")))
            if workflow is None:
                turn.tracker.clear_flow_state()
            else:
                return "active_workflow"
        if turn.tracker.active_agent_kind == "sub_agent":
            return "sticky_sub_agent"
        return "orchestrator"

    async def run_active_workflow_path(self) -> dict[str, Any]:
        turn = self._require_turn()
        flow_state = turn.tracker.active_flow_state
        if flow_state is None:
            return {"finished": True, "result": ChatGraphResult()}

        workflow = turn.bundle.find_workflow_by_id(str(flow_state.get("workflow_id", "")))
        if workflow is None:
            turn.tracker.clear_flow_state()
            return {"finished": False}

        result = await self._run_workflow_turn(
            workflow=workflow,
            tracker=turn.tracker,
            user_message=turn.user_message,
            enter_reason="active_state",
            trace=turn.trace,
        )
        return {"finished": True, "result": result}

    async def run_sticky_sub_agent_path(self) -> dict[str, Any]:
        turn = self._require_turn()
        sticky_result = await self._run_sticky_sub_agent_turn(
            bundle=turn.bundle,
            tracker=turn.tracker,
            user_message=turn.user_message,
            connectors_by_id=turn.connectors_by_id,
            tracing_context=turn.tracing_context,
            rag=turn.rag,
            trace=turn.trace,
            turn_evidence=turn.turn_evidence,
        )
        if sticky_result is None:
            return {"finished": False}
        return {"finished": True, "result": sticky_result}

    async def run_orchestrator_path(self) -> dict[str, Any]:
        turn = self._require_turn()
        turn_result = await self._orchestrator.run_turn(
            bundle=turn.bundle,
            tracker=turn.tracker,
            user_message=turn.user_message,
            system_prompt=turn.system_prompt,
            connectors_by_id=turn.connectors_by_id,
            tracing_context=turn.tracing_context,
            rag=turn.rag,
            trace=turn.trace,
            turn_evidence=turn.turn_evidence,
        )

        if turn_result.workflow_enter is not None:
            turn.workflow_enter = turn_result.workflow_enter.workflow
            turn.workflow_enter_reason = "orchestrator_tool"
            return {"finished": False, "needs_workflow_enter": True}

        if turn_result.delegation is not None:
            return {
                "finished": True,
                "result": ChatGraphResult(
                    replies=[WorkflowReply(text=reply) for reply in turn_result.replies],
                    routing=turn_result.routing,
                ),
            }

        return {
            "finished": True,
            "result": ChatGraphResult(
                replies=[WorkflowReply(text=reply) for reply in turn_result.replies],
                routing=turn_result.routing,
            ),
        }

    async def run_workflow_enter_path(self) -> dict[str, Any]:
        turn = self._require_turn()
        if turn.workflow_enter is None:
            return {"finished": True, "result": ChatGraphResult()}

        result = await self._enter_and_run_workflow(
            workflow=turn.workflow_enter,
            tracker=turn.tracker,
            user_message=turn.user_message,
            enter_reason=turn.workflow_enter_reason,
            trace=turn.trace,
        )
        return {"finished": True, "result": result}

    def _require_turn(self) -> _ChatTurnContext:
        if self._turn is None:
            raise RuntimeError("ChatGraph turn context is not set")
        return self._turn

    async def _run_sticky_sub_agent_turn(
        self,
        *,
        bundle: RuntimeBundle,
        tracker: Tracker,
        user_message: str,
        connectors_by_id: dict[str, dict[str, Any]],
        tracing_context: LlmTracingContext | None,
        rag: "RAGRetriever | None",
        trace: TraceCallback | None,
        turn_evidence: TurnEvidence,
    ) -> ChatGraphResult | None:
        sub_agent = bundle.orchestrator.find_sub_agent_by_id(tracker.active_agent_id)
        if sub_agent is None:
            tracker.reset_to_orchestrator()
            return None

        last_decision = tracker.last_routing_decision or {}
        delegate_args = dict(last_decision.get("args") or {})

        sub_runner = SubAgentRunner(tool_executor=self._orchestrator)
        sub_result = await sub_runner.run_turn(
            sub_agent=sub_agent,
            orchestrator=bundle.orchestrator,
            tracker=tracker,
            delegate_args=delegate_args,
            bundle=bundle,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
            turn_evidence=turn_evidence,
        )

        if sub_result.orchestrator_return:
            tracker.reset_to_orchestrator()
            return ChatGraphResult(
                replies=[WorkflowReply(text=reply) for reply in sub_result.replies],
                routing=sub_result.routing,
            )

        routing = {
            "mode": "delegate",
            "type": "delegate",
            "sub_agent_id": sub_agent.id,
            "sub_agent_name": sub_agent.name,
            "args": delegate_args,
            "sticky": True,
        }
        return ChatGraphResult(
            replies=[WorkflowReply(text=reply) for reply in sub_result.replies],
            routing=routing,
        )

    async def _enter_and_run_workflow(
        self,
        *,
        workflow: RuntimeWorkflow,
        tracker: Tracker,
        user_message: str,
        enter_reason: str,
        trace: TraceCallback | None,
    ) -> ChatGraphResult:
        initial_state = self._workflow_graph_runner.build_initial_state(workflow)
        if initial_state is None:
            return ChatGraphResult(
                replies=[WorkflowReply(text="This workflow is not configured correctly.")],
                routing={"mode": "orchestrator", "workflow_error": True},
            )

        tracker.enter_workflow(state=initial_state)
        if trace is not None:
            await trace(
                "workflow_enter",
                {
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "reason": enter_reason,
                },
            )

        result = await self._run_workflow_turn(
            workflow=workflow,
            tracker=tracker,
            user_message=user_message,
            enter_reason=enter_reason,
            trace=trace,
        )
        result.routing["enter_reason"] = enter_reason
        return result

    async def _run_workflow_turn(
        self,
        *,
        workflow: RuntimeWorkflow,
        tracker: Tracker,
        user_message: str,
        enter_reason: str,
        trace: TraceCallback | None,
    ) -> ChatGraphResult:
        state = tracker.active_flow_state
        if state is None:
            return ChatGraphResult(
                replies=[],
                routing={"mode": "orchestrator"},
            )

        result = await self._workflow_graph_runner.run_turn(
            workflow=workflow,
            state=state,
            user_message=user_message,
            trace=trace,
        )
        return await self._finalize_workflow_turn(
            tracker=tracker,
            result=result,
            enter_reason=enter_reason,
            trace=trace,
        )

    async def _finalize_workflow_turn(
        self,
        *,
        tracker: Tracker,
        result: WorkflowTurnResult,
        enter_reason: str,
        trace: TraceCallback | None,
    ) -> ChatGraphResult:
        if result.exited:
            tracker.clear_flow_state()
            if trace is not None:
                await trace(
                    "workflow_exit",
                    {
                        "workflow_id": result.routing.get("workflow_id"),
                        "reason": enter_reason,
                    },
                )
            routing = {
                "mode": "orchestrator",
                "type": "workflow",
                "workflow_exited": True,
                **result.routing,
            }
        else:
            tracker.set_active_flow_state(tracker.active_flow_state)
            routing = {
                **result.routing,
                "mode": "workflow",
                "type": "workflow",
            }

        return ChatGraphResult(replies=result.replies, routing=routing)
