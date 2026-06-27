import logging

from app.domain.constants.chat_constants import (
    ASSISTANT_UNAVAILABLE_MESSAGE,
    GENERIC_ERROR_MESSAGE,
    GUARDRAIL_REFUSAL_MESSAGE,
)
from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.pipeline.guardrails.runner import GuardrailRunner
from app.domain.pipeline.observability.trace import TraceCollector
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.domain.pipeline.sanitization.pii_redactor import redact_pii
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.assistant_loader import AssistantLoader
from app.services.runtime_bundle_loader import RuntimeBundleLoader
from app.services.tracker_service import TrackerService

logger = logging.getLogger(__name__)


class ChatCompletionService:
    def __init__(
        self,
        *,
        assistant_loader: AssistantLoader,
        tracker_service: TrackerService,
        runtime_bundle_loader: RuntimeBundleLoader,
        guardrails: GuardrailRunner | None = None,
        rag: RAGRetriever | None = None,
        orchestrator: OrchestratorRunner | None = None,
        trace: TraceCollector | None = None,
    ) -> None:
        self._assistant_loader = assistant_loader
        self._tracker_service = tracker_service
        self._runtime_bundle_loader = runtime_bundle_loader
        self._guardrails = guardrails or GuardrailRunner()
        self._rag = rag or RAGRetriever()
        self._orchestrator = orchestrator or OrchestratorRunner()
        self._trace = trace or TraceCollector()

    async def complete(self, *, webhook_id: str, request: ChatRequest) -> ChatResponse:
        try:
            return await self._complete_turn(webhook_id=webhook_id, request=request)
        except Exception:
            logger.exception("Chat completion failed for webhook_id=%s", webhook_id)
            return self._error_response(request.sender_id)

    async def _complete_turn(self, *, webhook_id: str, request: ChatRequest) -> ChatResponse:
        await self._trace.record(
            "input_message",
            {"sender_id": request.sender_id, "message": request.message},
        )

        resolved = await self._assistant_loader.try_resolve(
            webhook_id=webhook_id,
            metadata=request.metadata,
        )
        if resolved is None:
            return self._unavailable_response(request.sender_id)

        agent_id = str(resolved.agent_doc["_id"])
        tracker = await self._tracker_service.load_or_create(
            sender_id=request.sender_id,
            assistant_id=agent_id,
        )
        if tracker.active_agent_kind == "sub_agent":
            tracker.reset_to_orchestrator()

        bundle = await self._runtime_bundle_loader.load(agent_doc=resolved.agent_doc)
        await self._trace.record(
            "bundle_loaded",
            {
                "agent_id": agent_id,
                "tool_count": len(bundle.orchestrator.tools),
                "knowledge_base_count": len(bundle.orchestrator.knowledge_bases),
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
            await self._tracker_service.persist(tracker, replies)
            return ChatResponse(
                messages=[ChatMessage(recipient_id=request.sender_id, text=replies[0])],
            )

        await self._trace.record("guardrail_complete", {})

        tracker.append_user_message(message=sanitized_message, metadata=request.metadata)
        await self._tracker_service.save_session(tracker)

        kb_ids = [kb.id for kb in bundle.orchestrator.knowledge_bases]
        rag_context = await self._rag.retrieve(query=sanitized_message, knowledge_base_ids=kb_ids)
        await self._trace.record("rag_complete", {"context_length": len(rag_context)})

        guardrail_instructions = self._guardrails.build_instructions(bundle.orchestrator.guardrails)
        if guardrail_instructions:
            bundle.orchestrator.system_prompt = (
                bundle.orchestrator.system_prompt + "\n\n" + guardrail_instructions
            )

        connectors_by_id = await self._runtime_bundle_loader.load_connectors_for_tools(
            organization_id=bundle.organization_id,
            tools=bundle.orchestrator.tools,
        )

        replies = await self._orchestrator.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message=sanitized_message,
            rag_context=rag_context,
            connectors_by_id=connectors_by_id,
        )

        tracker.set_routing_decision(
            agent_id=agent_id,
            kind="orchestrator",
            decision={"mode": "orchestrator"},
        )
        await self._tracker_service.persist(tracker, replies)
        await self._trace.record("output_message", {"message_count": len(replies)})

        return ChatResponse(
            messages=[
                ChatMessage(recipient_id=request.sender_id, text=reply)
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
