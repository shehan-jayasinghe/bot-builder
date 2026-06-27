from app.infrastructure.ai.langsmith_tracing import LlmTracingContext, build_llm_run_config


def test_build_llm_run_config_disabled_when_tracing_off(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.infrastructure.ai.langsmith_tracing.settings.langchain_tracing_v2",
        False,
    )
    monkeypatch.setattr(
        "app.infrastructure.ai.langsmith_tracing.settings.langchain_api_key",
        "lsv2_test",
    )

    config = build_llm_run_config(
        LlmTracingContext(agent_id="agent-1", sender_id="user-1", source="preview"),
    )

    assert config is None


def test_build_llm_run_config_includes_metadata_and_tags(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.infrastructure.ai.langsmith_tracing.settings.langchain_tracing_v2",
        True,
    )
    monkeypatch.setattr(
        "app.infrastructure.ai.langsmith_tracing.settings.langchain_api_key",
        "lsv2_test",
    )

    config = build_llm_run_config(
        LlmTracingContext(
            agent_id="agent-1",
            sender_id="preview-session-abc",
            source="preview",
            organization_id="org-1",
            model_id="amazon.nova-lite-v1:0",
            region="us-east-1",
        ),
    )

    assert config is not None
    assert config["run_name"] == "preview:agent-1"
    assert config["tags"] == ["bot-builder", "preview"]
    assert config["metadata"] == {
        "agent_id": "agent-1",
        "sender_id": "preview-session-abc",
        "source": "preview",
        "organization_id": "org-1",
        "model_id": "amazon.nova-lite-v1:0",
        "region": "us-east-1",
    }
