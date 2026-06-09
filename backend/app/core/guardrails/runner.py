class GuardrailRunner:
    async def check(self, *, user_message: str, system_prompt: str) -> None:
        """
        Run safety / policy checks before LLM inference.

        TODO:
          - LLM or rule-based guardrail
          - emit trace event: guardrail_complete
          - raise or block on policy violations
        """
        _ = user_message, system_prompt
        pass
