from __future__ import annotations

from typing import Any

# Custom detectors — LangChain PIIMiddleware regex `detector=` strings.
_API_KEY_PATTERN = r"(?:sk-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16})"
_PASSWORD_PATTERN = r"(?i)(?:password|passwd|pwd)\s*[:=]\s*\S+"
_OTP_PATTERN = r"(?i)(?:otp|one[- ]time(?:\s+password)?|pin\s*code)\s*[:=]?\s*\d{4,8}\b"

PII_BLOCKED_USER_MESSAGE = (
    "Please don't share passwords, OTPs, or API keys in chat. "
    "I can still help with your account or payments another way."
)


def build_agent_pii_middleware() -> list[Any]:
    """LangChain PIIMiddleware on create_agent() — built-in + regex secret detectors."""
    from langchain.agents.middleware import PIIMiddleware

    return [
        PIIMiddleware(
            "email",
            strategy="redact",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "ip",
            strategy="redact",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "url",
            strategy="redact",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "api_key",
            detector=_API_KEY_PATTERN,
            strategy="block",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "password",
            detector=_PASSWORD_PATTERN,
            strategy="block",
            apply_to_input=True,
            apply_to_output=True,
        ),
        PIIMiddleware(
            "otp",
            detector=_OTP_PATTERN,
            strategy="block",
            apply_to_input=True,
            apply_to_output=True,
        ),
    ]
