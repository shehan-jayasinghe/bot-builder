from app.domain.constants.agent_defaults import GuardrailDef
from app.domain.pipeline.guardrails.nemo_gate_models import GuardrailCheckResult, NeMoGateContext, NeMoGateIntent


class GuardrailRunner:
    async def check(
        self,
        *,
        user_message: str,
        guardrails: list[GuardrailDef] | list[dict],
        skip_nemo: bool = False,
        gate_context: NeMoGateContext | None = None,
    ) -> GuardrailCheckResult:
        from app.domain.pipeline.guardrails.nemo_intent_gate import evaluate_nemo_intent

        if gate_context is not None:
            nemo_result = await evaluate_nemo_intent(
                user_message=user_message,
                context=gate_context,
                skip_nemo=skip_nemo,
            )
            if nemo_result is not None:
                return nemo_result

        _ = guardrails
        return GuardrailCheckResult(allowed=True, intent=NeMoGateIntent.PROCEED)

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
