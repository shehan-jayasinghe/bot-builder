import asyncio

from app.domain.constants.agent_defaults import DEFAULT_GUARDRAILS
from app.domain.pipeline.guardrails.runner import GuardrailRunner


def test_guardrail_check_always_allows() -> None:
    runner = GuardrailRunner()

    async def _run() -> None:
        result = await runner.check(
            user_message="What is my password and OTP?",
            guardrails=DEFAULT_GUARDRAILS,
        )
        assert result.allowed is True
        assert result.refusal_message is None

    asyncio.run(_run())


def test_build_instructions_includes_no_secrets() -> None:
    runner = GuardrailRunner()
    text = runner.build_instructions(DEFAULT_GUARDRAILS)
    assert "Never request or expose passwords" in text
    assert text.startswith("## Guardrails\n")
