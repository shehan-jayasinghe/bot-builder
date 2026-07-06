from app.domain.graph.langchain.pii_middleware import build_agent_pii_middleware


def test_build_agent_pii_middleware_includes_expected_types() -> None:
    middleware = build_agent_pii_middleware()
    pii_types = {item.pii_type for item in middleware}
    assert pii_types == {
        "email",
        "credit_card",
        "ip",
        "url",
        "api_key",
        "password",
        "otp",
    }


def test_secret_pii_middleware_blocks_on_input() -> None:
    middleware = build_agent_pii_middleware()
    by_type = {item.pii_type: item for item in middleware}

    assert by_type["email"].strategy == "redact"
    assert by_type["credit_card"].strategy == "mask"
    assert by_type["ip"].strategy == "redact"
    assert by_type["url"].strategy == "redact"
    assert by_type["api_key"].strategy == "block"
    assert by_type["password"].strategy == "block"
    assert by_type["otp"].strategy == "block"
    assert by_type["api_key"].apply_to_input is True
    assert by_type["password"].apply_to_input is True


def test_agent_factory_wires_pii_middleware() -> None:
    import inspect

    source = inspect.getsource(
        __import__("app.domain.graph.langchain.agent_factory", fromlist=["create_bot_agent"]),
    )
    assert "build_agent_pii_middleware" in source
