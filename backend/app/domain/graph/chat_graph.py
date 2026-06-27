from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.graph.turn_result import AgentTurnResult
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeWorkflow
from app.domain.models.tracker import Tracker
from app.domain.workflow.workflow_runner import WorkflowReply, WorkflowRunner, WorkflowTurnResult
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext

if TYPE_CHECKING:
    from app.domain.pipeline.rag.retriever import RAGRetriever

TraceCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass
class ChatGraphResult:
    replies: list[WorkflowReply] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=lambda: {"mode": "orchestrator"})


class ChatGraph:
    def __init__(
        self,
        *,
        orchestrator: OrchestratorRunner | None = None,
        workflow_runner: WorkflowRunner | None = None,
    ) -> None:
        self._orchestrator = orchestrator or OrchestratorRunner()
        self._workflow_runner = workflow_runner or WorkflowRunner()

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
        flow_state = tracker.active_flow_state
        if flow_state is not None:
            workflow = bundle.find_workflow_by_id(str(flow_state.get("workflow_id", "")))
            if workflow is None:
                tracker.clear_flow_state()
            else:
                return await self._run_workflow_turn(
                    workflow=workflow,
                    tracker=tracker,
                    user_message=user_message,
                    enter_reason="active_state",
                    trace=trace,
                )

        turn_result = await self._orchestrator.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message=user_message,
            system_prompt=system_prompt,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=rag,
            trace=trace,
        )

        if turn_result.workflow_enter is not None:
            return await self._enter_and_run_workflow(
                workflow=turn_result.workflow_enter.workflow,
                tracker=tracker,
                user_message=user_message,
                enter_reason="orchestrator_tool",
                trace=trace,
            )

        if turn_result.delegation is not None:
            return ChatGraphResult(
                replies=[WorkflowReply(text=reply) for reply in turn_result.replies],
                routing=turn_result.routing,
            )

        return ChatGraphResult(
            replies=[WorkflowReply(text=reply) for reply in turn_result.replies],
            routing=turn_result.routing,
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
        initial_state = self._workflow_runner.build_initial_state(workflow)
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

        result = await self._workflow_runner.run_turn(
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
