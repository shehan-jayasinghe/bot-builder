import inspect


def test_pii_middleware_uses_langchain_builtin_types_only() -> None:
    source = inspect.getsource(
        __import__(
            "app.domain.graph.langchain.pii_middleware",
            fromlist=["build_agent_pii_middleware"],
        ),
    )
    assert "PIIMiddleware" in source
    assert '"email"' in source
    assert '"credit_card"' in source
    assert "re.compile" not in source
    assert "detector=" not in source


def test_agent_factory_wires_pii_middleware() -> None:
    source = inspect.getsource(
        __import__("app.domain.graph.langchain.agent_factory", fromlist=["create_bot_agent"]),
    )
    assert "build_agent_pii_middleware" in source
