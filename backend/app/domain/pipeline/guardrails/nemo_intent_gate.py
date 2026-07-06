import logging
import re

from app.config import settings
from app.domain.constants.chat_constants import GUARDRAIL_REFUSAL_MESSAGE
from app.domain.pipeline.guardrails.runner import GuardrailCheckResult

logger = logging.getLogger(__name__)

_GREETING = re.compile(
    r"^\s*(hi|hello|hey|good\s+(morning|afternoon))\s*[!?.]*\s*$",
    re.IGNORECASE,
)
_HELP = re.compile(
    r"^\s*(help|what can you do|how can you help)\s*[!?.]*\s*$",
    re.IGNORECASE,
)
_BYE = re.compile(
    r"^\s*(bye|goodbye|see you)\s*[!?.]*\s*$",
    re.IGNORECASE,
)

_SCRIPTED_REPLIES: dict[str, str] = {
    "greeting": "Hello! How can I help you with your account or payments today?",
    "help": "I can help with payment reminders, account questions, and guided workflows. What do you need?",
    "bye": "Goodbye! Reach out anytime if you need help with your account.",
}


def match_local_scripted(message: str) -> str | None:
    text = message.strip()
    if _GREETING.match(text):
        return _SCRIPTED_REPLIES["greeting"]
    if _HELP.match(text):
        return _SCRIPTED_REPLIES["help"]
    if _BYE.match(text):
        return _SCRIPTED_REPLIES["bye"]
    return None


async def evaluate_nemo_intent(
    *,
    user_message: str,
    skip_nemo: bool = False,
) -> GuardrailCheckResult | None:
    """Run NeMo intent gate when enabled. Returns None when NeMo is off."""
    if not settings.nemo_guardrails_enabled or skip_nemo:
        return None

    scripted = match_local_scripted(user_message)
    if scripted:
        return GuardrailCheckResult(allowed=False, scripted_reply=scripted)

    try:
        from nemoguardrails.rails.llm.options import RailStatus, RailType

        from app.domain.pipeline.guardrails.nemo_runtime import get_nemo_rails

        rails = get_nemo_rails()
        result = await rails.check_async(
            [{"role": "user", "content": user_message}],
            rail_types=[RailType.INPUT],
        )
        if result.status == RailStatus.BLOCKED:
            refusal = (result.content or "").strip() or GUARDRAIL_REFUSAL_MESSAGE
            return GuardrailCheckResult(allowed=False, refusal_message=refusal)
    except Exception:
        logger.exception("NeMo intent gate failed; allowing message through")
        return GuardrailCheckResult(allowed=True)

    return GuardrailCheckResult(allowed=True)
