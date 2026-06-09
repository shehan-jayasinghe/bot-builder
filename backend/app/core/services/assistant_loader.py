from typing import Any

from app.core.models.assistant import DialogueAssistant


class AssistantLoader:
    async def load(self, *, webhook_id: str, metadata: dict[str, Any]) -> DialogueAssistant:
        """
        Load assistant configuration for a channel webhook.

        TODO:
          - fetch from MongoDB by webhook_id
          - resolve organization / channel context from metadata
          - decrypt secrets if any
          - load flows, slots, knowledge base references
        """
        _ = metadata  # reserved for channel-specific routing later

        # MVP stub so the main flow works while you learn each step
        return DialogueAssistant(
            id="stub-assistant-id",
            name="Demo Bot",
            webhook_id=webhook_id,
            system_prompt="You are a helpful assistant for ShoutOUT Bot Builder.",
        )
