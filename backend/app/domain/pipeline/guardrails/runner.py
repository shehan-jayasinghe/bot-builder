from dataclasses import dataclass

from app.domain.constants.agent_defaults import GuardrailDef


@dataclass(frozen=True)
class GuardrailCheckResult:
    allowed: bool
    refusal_message: str | None = None
    scripted_reply: str | None = None


class GuardrailRunner:
    async def check(
        self,
        *,
        user_message: str,
        guardrails: list[GuardrailDef] | list[dict],
        skip_nemo: bool = False,
    ) -> GuardrailCheckResult:
        from app.domain.pipeline.guardrails.nemo_intent_gate import evaluate_nemo_intent

        nemo_result = await evaluate_nemo_intent(
            user_message=user_message,
            skip_nemo=skip_nemo,
        )
        if nemo_result is not None:
            return nemo_result

        _ = guardrails
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
