import re

_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
)
_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}(?!\d)",
)
_API_KEY_PATTERN = re.compile(
    r"\b(?:sk|api)[-_]?[a-zA-Z0-9]{16,}\b",
    re.IGNORECASE,
)


def redact_pii(text: str) -> str:
    """Redact common PII patterns before LLM inference and tracker storage."""
    redacted = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    redacted = _PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)
    redacted = _API_KEY_PATTERN.sub("[REDACTED_SECRET]", redacted)
    return redacted
