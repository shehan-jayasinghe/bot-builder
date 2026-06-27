import logging
from typing import Any

from app.domain.constants.chat_constants import (
    ASSISTANT_UNAVAILABLE_MESSAGE,
    GENERIC_ERROR_MESSAGE,
    GUARDRAIL_REFUSAL_MESSAGE,
)
from app.domain.graph.chat_graph import ChatGraph
from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.pipeline.guardrails.runner import GuardrailRunner
from app.domain.pipeline.observability.trace import TraceCollector
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.domain.pipeline.sanitization.pii_redactor import redact_pii
from app.infrastructure.ai.langsmith_tracing import LlmTracingContext
from app.infrastructure.db.repositories.mongo.agent_repository import AgentRepository
from app.schemas.chat import ChatButton, ChatMessage, ChatRequest, ChatResponse
from app.services.assistant_loader import AssistantLoader
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.services.tracker_service import TrackerService
from app.shared.exceptions.agent import AgentNotFoundError

logger = logging.getLogger(__name__)

CHAT_SOURCE_WEBHOOK = "webhook"
CHAT_SOURCE_PREVIEW = "preview"


class ChatCompletionService:
    def __init__(
        self,
        *,
        assistant_loader: AssistantLoader,
        agent_repository: AgentRepository,
        tracker_service: TrackerService,
        runtime_bundle_loader: RuntimeBundleLoader,
        guardrails: GuardrailRunner | None = None,
        rag: RAGRetriever | None = None,
        orchestrator: OrchestratorRunner | None = None,
        chat_graph: ChatGraph | None = None,
        trace: TraceCollector | None = None,
    ) -> None:
        self._assistant_loader = assistant_loader
        self._agent_repository = agent_repository
        self._tracker_service = tracker_service
        self._runtime_bundle_loader = runtime_bundle_loader
        self._guardrails = guardrails or GuardrailRunner()
        self._rag = rag or RAGRetriever()
        self._orchestrator = orchestrator or OrchestratorRunner()
        self._chat_graph = chat_graph or ChatGraph(orchestrator=self._orchestrator)
        self._trace = trace or TraceCollector()

    async def complete(self, *, webhook_id: str, request: ChatRequest) -> ChatResponse:
        try:
            resolved = await self._assistant_loader.try_resolve(
                webhook_id=webhook_id,
                metadata=request.metadata,
            )
            if resolved is None:
                return self._unavailable_response(request.sender_id)
            return await self._complete_turn(
                agent_doc=resolved.agent_doc,
                request=request,
                source=CHAT_SOURCE_WEBHOOK,
            )
        except Exception:
            logger.exception("Chat completion failed for webhook_id=%s", webhook_id)
            return self._error_response(request.sender_id)

    async def complete_preview(
        self,
        *,
        agent_id: str,
        organization_id: str,
        request: ChatRequest,
    ) -> ChatResponse:
        agent_doc = await self._agent_repository.find_by_id_for_organization(
            agent_id=agent_id,
            organization_id=organization_id,
        )
        if agent_doc is None:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")

        try:
            return await self._complete_turn(
                agent_doc=agent_doc,
                request=request,
                source=CHAT_SOURCE_PREVIEW,
            )
        except Exception:
            logger.exception("Preview chat failed for agent_id=%s", agent_id)
            return self._error_response(request.sender_id)

    async def _complete_turn(
        self,
        *,
        agent_doc: dict[str, Any],
        request: ChatRequest,
        source: str,
    ) -> ChatResponse:
        agent_id = str(agent_doc["_id"])
        self._trace.begin_turn()

        await self._trace.record(
            "input_message",
            {"sender_id": request.sender_id, "message": request.message},
        )

        tracker = await self._tracker_service.load_or_create(
            sender_id=request.sender_id,
            assistant_id=agent_id,
            source=source,
            organization_id=str(agent_doc["organization_id"]),
        )
        self._trace.bind_tracker(tracker)

        if tracker.active_agent_kind == "sub_agent" and tracker.active_flow_state is None:
            tracker.reset_to_orchestrator()

        bundle = await self._runtime_bundle_loader.load(
            agent_doc=agent_doc,
            for_preview=source == CHAT_SOURCE_PREVIEW,
        )
        await self._trace.record(
            "bundle_loaded",
            {
                "agent_id": agent_id,
                "tool_count": len(bundle.orchestrator.tools),
                "knowledge_base_count": len(bundle.orchestrator.knowledge_bases),
                "sub_agent_count": len(bundle.orchestrator.sub_agents),
                "workflow_count": len(bundle.orchestrator.workflows),
            },
        )

        sanitized_message = redact_pii(request.message)
        guardrail_result = await self._guardrails.check(
            user_message=sanitized_message,
            guardrails=bundle.orchestrator.guardrails,
        )
        if not guardrail_result.allowed:
            await self._trace.record("guardrail_blocked", {})
            replies = [guardrail_result.refusal_message or GUARDRAIL_REFUSAL_MESSAGE]
            tracker.append_user_message(message=sanitized_message, metadata=request.metadata)
            routing = {"mode": "orchestrator", "blocked": True}
            tracker.set_routing_decision(agent_id=agent_id, kind="orchestrator", decision=routing)
            await self._trace.record(
                "output_message",
                _output_message_trace_data(replies),
            )
            self._trace.finish_turn(routing_decision=routing)
            await self._tracker_service.persist(tracker, replies)
            return ChatResponse(
                messages=[ChatMessage(recipient_id=request.sender_id, text=replies[0])],
            )

        await self._trace.record("guardrail_complete", {})

        tracker.append_user_message(message=sanitized_message, metadata=request.metadata)
        await self._tracker_service.save_session(tracker)

        in_workflow = tracker.active_flow_state is not None
        will_auto_start_workflow = (
            not in_workflow
            and bool(bundle.orchestrator.workflows)
            and sum(1 for event in tracker.get_history() if event.get("role") == "user") == 1
        )
        skip_rag = in_workflow or will_auto_start_workflow

        kb_list = bundle.orchestrator.knowledge_bases
        if skip_rag or not kb_list:
            await self._trace.record("rag_skipped", {})
            rag_context = ""
        else:
            rag_result = await self._rag.retrieve(
                query=sanitized_message,
                knowledge_bases=kb_list,
                organization_id=bundle.organization_id,
            )
            rag_context = rag_result.context
            if rag_result.error and not rag_context:
                await self._trace.record("rag_error", {"detail": rag_result.error})
            else:
                trace_data: dict[str, object] = {
                    "context_length": len(rag_context),
                    "kb_ids": rag_result.kb_ids,
                    "chunk_count": rag_result.chunk_count,
                    "storage_types": rag_result.storage_types,
                }
                if rag_result.error:
                    trace_data["partial_error"] = rag_result.error
                await self._trace.record("rag_complete", trace_data)

        guardrail_instructions = self._guardrails.build_instructions(bundle.orchestrator.guardrails)
        if guardrail_instructions:
            bundle.orchestrator.system_prompt = (
                bundle.orchestrator.system_prompt + "\n\n" + guardrail_instructions
            )

        connectors_by_id = await self._runtime_bundle_loader.load_connectors_for_tools(
            organization_id=bundle.organization_id,
            tools=bundle.all_runtime_tools(),
        )

        llm_config = bundle.orchestrator.llm_config
        tracing_context = LlmTracingContext(
            agent_id=agent_id,
            sender_id=request.sender_id,
            source=source,
            organization_id=str(agent_doc["organization_id"]),
            model_id=llm_config.model_id if llm_config else None,
            region=llm_config.region if llm_config else None,
        )

        turn_result = await self._chat_graph.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message=sanitized_message,
            rag_context=rag_context,
            connectors_by_id=connectors_by_id,
            tracing_context=tracing_context,
            rag=self._rag,
            trace=self._trace.record,
        )
        replies = turn_result.replies
        routing = turn_result.routing

        if routing.get("mode") == "delegate":
            await self._trace.record(
                "sub_agent_start",
                {
                    "sub_agent_id": routing.get("sub_agent_id"),
                    "sub_agent_name": routing.get("sub_agent_name"),
                    "args": routing.get("args"),
                },
            )
            await self._trace.record("sub_agent_complete", {"reply_count": len(replies)})

        tracker.set_routing_decision(
            agent_id=str(routing.get("sub_agent_id", agent_id)),
            kind=(
                "sub_agent"
                if routing.get("mode") == "delegate"
                else "workflow"
                if routing.get("mode") == "workflow"
                else "orchestrator"
            ),
            decision=routing,
        )
        await self._trace.record(
            "output_message",
            _output_message_trace_data(replies),
        )
        self._trace.finish_turn(routing_decision=routing)
        reply_texts = [reply.text for reply in replies if reply.text]
        await self._tracker_service.persist(tracker, reply_texts)

        return ChatResponse(
            messages=[
                ChatMessage(
                    recipient_id=request.sender_id,
                    text=reply.text,
                    buttons=(
                        [ChatButton(**button) for button in reply.buttons]
                        if reply.buttons
                        else None
                    ),
                )
                for reply in replies
            ],
        )

    @staticmethod
    def _unavailable_response(sender_id: str) -> ChatResponse:
        return ChatResponse(
            messages=[
                ChatMessage(
                    recipient_id=sender_id,
                    text=ASSISTANT_UNAVAILABLE_MESSAGE,
                ),
            ],
        )

    @staticmethod
    def _error_response(sender_id: str) -> ChatResponse:
        return ChatResponse(
            messages=[
                ChatMessage(recipient_id=sender_id, text=GENERIC_ERROR_MESSAGE),
            ],
        )


def _output_message_trace_data(replies: list[Any]) -> dict[str, object]:
    texts = [reply.text for reply in replies if getattr(reply, "text", None)]
    data: dict[str, object] = {"message_count": len(texts)}
    if len(texts) == 1:
        data["text"] = texts[0]
    elif texts:
        data["texts"] = texts
    return data
