from app.domain.pipeline.sanitization.pii_redactor import redact_pii


def test_redact_pii_masks_email_and_phone() -> None:
    text = "Contact me at john@example.com or +1 555-123-4567"
    redacted = redact_pii(text)
    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
