from __future__ import annotations

from typing import Any


def build_agent_pii_middleware() -> list[Any]:
    """LangChain PIIMiddleware on create_agent() — built-in detectors only."""
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
    ]
