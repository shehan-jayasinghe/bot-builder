from app.infrastructure.ai.llm import BedrockLLM
from app.domain.engine.slot_extractor import SlotExtractor
from app.domain.models.tracker import Tracker
from app.domain.models.assistant import DialogueAssistant


class FlowManager:
    def __init__(
        self,
        assistant: DialogueAssistant,
        tracker: Tracker,
        user_message: str,
        llm: BedrockLLM | None = None,
        slot_extractor: SlotExtractor | None = None,
    ) -> None:
        self._assistant = assistant
        self._tracker = tracker
        self._user_message = user_message
        self._llm = llm or BedrockLLM(
            temperature=assistant.temperature,
            max_output_tokens=assistant.max_output_tokens,
        )
        self._slot_extractor = slot_extractor or SlotExtractor()

    async def handle_message(self) -> list[str]:
        """
        Main inference logic for a text message.

        TODO (later):
          - classify intent and pick the right flow
          - run slot extraction before LLM call
          - RAG retrieval from Qdrant
          - execute flow nodes: branch, utter, prompt, action
        """
        # TODO: use active flow state from tracker
        history = self._tracker.get_history()

        # TODO: run slot extraction
        # slots = await self._slot_extractor.extract(
        #     assistant=self._assistant,
        #     user_message=self._user_message,
        #     history=history,
        # )

        # TODO: retrieve context from knowledge base (RAG)
        # rag_context = await self._retrieve_context()

        system_prompt = self._assistant.system_prompt

        reply = await self._llm.chat(
            system_prompt=system_prompt,
            user_message=self._user_message,
            history=history,
        )

        # TODO: handle multiple response types (buttons, cards, images)
        return [reply]

    async def handle_payload(self, payload_content: str) -> list[str]:
        """
        Handle button clicks / structured payloads.

        TODO: route payload to the correct flow node
        """
        _ = payload_content
        return ["Payload handling is not implemented yet."]
