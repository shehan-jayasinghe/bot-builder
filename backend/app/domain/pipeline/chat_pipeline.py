from app.domain.engine.dialogue import DialogueEngine
from app.domain.pipeline.guardrails.runner import GuardrailRunner
from app.domain.pipeline.observability.trace import TraceCollector
from app.domain.pipeline.rag.retriever import RAGRetriever
from app.domain.pipeline.skills.router import SkillRouter
from app.schemas.chat import ChatMessage


class ChatPipeline:
    """Runs pre/post steps around DialogueEngine for a single chat turn."""

    def __init__(
        self,
        guardrails: GuardrailRunner | None = None,
        rag: RAGRetriever | None = None,
        skills: SkillRouter | None = None,
        trace: TraceCollector | None = None,
    ) -> None:
        self._guardrails = guardrails or GuardrailRunner()
        self._rag = rag or RAGRetriever()
        self._skills = skills or SkillRouter()
        self._trace = trace or TraceCollector()

    async def run(self, engine: DialogueEngine) -> list[ChatMessage]:
        await self._trace.record(
            "input_message",
            {"sender_id": engine.sender_id, "message": engine.message},
        )

        await self._guardrails.check(
            user_message=engine.message,
            system_prompt=engine.assistant.system_prompt,
        )
        await self._trace.record("guardrail_complete", {})

        # TODO: load knowledge_base_ids from assistant config
        rag_context = await self._rag.retrieve(
            query=engine.message,
            knowledge_base_ids=[],
        )
        await self._trace.record("rag_complete", {"context_length": len(rag_context)})

        # TODO: load skills from assistant config
        skill_result = await self._skills.route(
            user_message=engine.message,
            skills=[],
        )
        if skill_result is not None:
            await self._trace.record("tool_start", {"skill": skill_result})

        # TODO: pass rag_context and skill_result into FlowManager
        messages = await engine.run()

        await self._trace.record("output_message", {"message_count": len(messages)})
        return messages
