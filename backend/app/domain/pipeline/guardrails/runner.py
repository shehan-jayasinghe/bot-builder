from dataclasses import dataclass
import re

from app.domain.constants.agent_defaults import GuardrailDef
from app.domain.constants.chat_constants import GUARDRAIL_REFUSAL_MESSAGE

_SECRET_REQUEST_PATTERN = re.compile(
    r"\b(password|otp|one[- ]time|pin\s*code|cvv|cvc|card\s*number)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GuardrailCheckResult:
    allowed: bool
    refusal_message: str | None = None


class GuardrailRunner:
    async def check(
        self,
        *,
        user_message: str,
        guardrails: list[GuardrailDef] | list[dict],
    ) -> GuardrailCheckResult:
        enabled = {
            item["key"]: item
            for item in guardrails
            if isinstance(item, dict) and item.get("enabled", True)
        }

        if "no_secrets" in enabled and _SECRET_REQUEST_PATTERN.search(user_message):
            return GuardrailCheckResult(
                allowed=False,
                refusal_message=GUARDRAIL_REFUSAL_MESSAGE,
            )

        return GuardrailCheckResult(allowed=True)

    def build_instructions(self, guardrails: list[GuardrailDef] | list[dict]) -> str:
        lines: list[str] = []
        for item in guardrails:
            if not isinstance(item, dict):
                continue
            if not item.get("enabled", True):
                continue
            instruction = item.get("instruction")
            if instruction:
                lines.append(str(instruction))
        if not lines:
            return ""
        return "## Guardrails\n" + "\n".join(f"- {line}" for line in lines)
