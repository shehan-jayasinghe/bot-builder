import logging
from typing import TypeVar

from app.config import settings
from app.domain.constants.chat_constants import GUARDRAIL_REFUSAL_MESSAGE
from app.domain.pipeline.guardrails.nemo_gate_models import NeMoGateContext, NeMoOutputCheckResult

logger = logging.getLogger(__name__)

TReply = TypeVar("TReply")


async def evaluate_nemo_output(
    *,
    user_message: str,
    assistant_reply: str,
    context: NeMoGateContext,
) -> NeMoOutputCheckResult:
    """Run NeMo output self-check when enabled. Returns allowed=True when NeMo is off."""
    _ = context
    if not settings.nemo_guardrails_enabled:
        return NeMoOutputCheckResult(allowed=True)

    text = assistant_reply.strip()
    if not text:
        return NeMoOutputCheckResult(allowed=True)

    try:
        from nemoguardrails.rails.llm.options import RailStatus, RailType

        from app.domain.pipeline.guardrails.nemo_runtime import get_nemo_rails

        rails = get_nemo_rails()
        result = await rails.check_async(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": text},
            ],
            rail_types=[RailType.OUTPUT],
        )
        if result.status == RailStatus.BLOCKED:
            refusal = (result.content or "").strip() or GUARDRAIL_REFUSAL_MESSAGE
            return NeMoOutputCheckResult(
                allowed=False,
                refusal_message=refusal,
                rail=result.rail,
            )
    except Exception:
        logger.exception("NeMo output gate failed; allowing reply through")
        return NeMoOutputCheckResult(allowed=True)

    return NeMoOutputCheckResult(allowed=True)


async def apply_nemo_output_gate(
    *,
    user_message: str,
    replies: list[TReply],
    context: NeMoGateContext,
) -> tuple[list[TReply], NeMoOutputCheckResult]:
    """Check each reply with text; replace blocked replies with refusal."""
    if not settings.nemo_guardrails_enabled or not replies:
        return replies, NeMoOutputCheckResult(allowed=True)

    checked: list[TReply] = []
    any_blocked = False
    blocked_rail: str | None = None
    refusal_message: str | None = None

    for reply in replies:
        text = getattr(reply, "text", None)
        if not text or not str(text).strip():
            checked.append(reply)
            continue

        result = await evaluate_nemo_output(
            user_message=user_message,
            assistant_reply=str(text),
            context=context,
        )
        if not result.allowed:
            any_blocked = True
            blocked_rail = result.rail
            refusal_message = result.refusal_message
            checked.append(
                _replace_reply_text(reply, refusal_message or GUARDRAIL_REFUSAL_MESSAGE),
            )
        else:
            checked.append(reply)

    if any_blocked:
        return checked, NeMoOutputCheckResult(
            allowed=False,
            refusal_message=refusal_message,
            rail=blocked_rail,
        )
    return checked, NeMoOutputCheckResult(allowed=True)


def _replace_reply_text(reply: TReply, text: str) -> TReply:
    from dataclasses import replace

    return replace(reply, text=text)
