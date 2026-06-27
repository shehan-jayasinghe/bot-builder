from app.domain.graph.orchestrator import OrchestratorRunner
from app.domain.models.runtime_bundle import RuntimeBundle
from app.domain.models.tracker import Tracker
from app.domain.pipeline.guardrails.runner import GuardrailRunner
from app.domain.pipeline.observability.trace import TraceCollector
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.domain.pipeline.sanitization.pii_redactor import redact_pii
from app.schemas.chat import ChatMessage


class ChatPipeline:
    """Pre/post steps around orchestrator inference for a single chat turn."""

    def __init__(
        self,
        guardrails: GuardrailRunner | None = None,
        rag: RAGRetriever | None = None,
        orchestrator: OrchestratorRunner | None = None,
        trace: TraceCollector | None = None,
    ) -> None:
        self._guardrails = guardrails or GuardrailRunner()
        self._rag = rag or RAGRetriever()
        self._orchestrator = orchestrator or OrchestratorRunner()
        self._trace = trace or TraceCollector()

    async def run_turn(
        self,
        *,
        bundle: RuntimeBundle,
        tracker: Tracker,
        user_message: str,
        connectors_by_id: dict,
    ) -> list[str]:
        sanitized_message = redact_pii(user_message)
        guardrail_result = await self._guardrails.check(
            user_message=sanitized_message,
            guardrails=bundle.orchestrator.guardrails,
        )
        await self._trace.record(
            "guardrail_complete" if guardrail_result.allowed else "guardrail_blocked",
            {},
        )
        if not guardrail_result.allowed:
            return [guardrail_result.refusal_message or "I can't help with that request."]

        kb_list = bundle.orchestrator.knowledge_bases
        if not kb_list:
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
                await self._trace.record(
                    "rag_complete",
                    {
                        "context_length": len(rag_context),
                        "kb_ids": rag_result.kb_ids,
                        "chunk_count": rag_result.chunk_count,
                        "storage_types": rag_result.storage_types,
                    },
                )

        guardrail_instructions = self._guardrails.build_instructions(bundle.orchestrator.guardrails)
        if guardrail_instructions:
            bundle.orchestrator.system_prompt = (
                bundle.orchestrator.system_prompt + "\n\n" + guardrail_instructions
            )

        turn_result = await self._orchestrator.run_turn(
            bundle=bundle,
            tracker=tracker,
            user_message=sanitized_message,
            rag_context=rag_context,
            connectors_by_id=connectors_by_id,
            rag=self._rag,
        )
        replies = turn_result.replies
        await self._trace.record("output_message", {"message_count": len(replies)})
        return replies

    @staticmethod
    def to_chat_messages(*, sender_id: str, replies: list[str]) -> list[ChatMessage]:
        return [ChatMessage(recipient_id=sender_id, text=reply) for reply in replies]
