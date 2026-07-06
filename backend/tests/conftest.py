import pytest


@pytest.fixture(autouse=True)
def nemo_guardrails_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests should not depend on local .env enabling NeMo."""
    monkeypatch.setattr("app.config.settings.nemo_guardrails_enabled", False)
