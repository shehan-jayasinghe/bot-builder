import logging

from app.config import settings
from app.domain.constants.chat_constants import GUARDRAIL_REFUSAL_MESSAGE
from app.domain.pipeline.guardrails.nemo_gate_models import (
    GuardrailCheckResult,
    NeMoGateContext,
    NeMoGateIntent,
)
from app.domain.pipeline.guardrails.scripted_intents import match_scripted_intent

logger = logging.getLogger(__name__)


def build_gate_context(
    *,
    agent_name: str,
    industry: str | None = None,
    description: str | None = None,
) -> NeMoGateContext:
    return NeMoGateContext(
        agent_name=agent_name,
        industry=industry,
        description=description,
    )


async def evaluate_nemo_intent(
    *,
    user_message: str,
    context: NeMoGateContext,
    skip_nemo: bool = False,
) -> GuardrailCheckResult | None:
    """Run NeMo intent gate when enabled. Returns None when NeMo is off."""
    if not settings.nemo_guardrails_enabled or skip_nemo:
        return None

    scripted = match_scripted_intent(user_message, context=context)
    if scripted is not None:
        return GuardrailCheckResult(
            allowed=False,
            intent=scripted.intent,
            scripted_reply=scripted.reply,
            matched_phrase=scripted.matched_phrase,
        )

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
            return GuardrailCheckResult(
                allowed=False,
                intent=NeMoGateIntent.BLOCKED,
                refusal_message=refusal,
                rail=result.rail,
            )
    except Exception:
        logger.exception("NeMo intent gate failed; allowing message through")
        return GuardrailCheckResult(allowed=True, intent=NeMoGateIntent.PROCEED)

    return GuardrailCheckResult(allowed=True, intent=NeMoGateIntent.PROCEED)
