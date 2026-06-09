from typing import Any

from app.core.models.assistant import DialogueAssistant


class SlotExtractor:
    """
    Extract structured slots from user messages.

    TODO:
      - define slot schemas per assistant
      - use Bedrock structured output or tool calling
      - merge extracted slots into tracker state
    """

    async def extract(
        self,
        *,
        assistant: DialogueAssistant,
        user_message: str,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        _ = assistant, user_message, history
        return {}
