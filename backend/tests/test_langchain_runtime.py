import inspect
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT / "app"


def test_orchestrator_agent_uses_create_agent() -> None:
    factory_source = inspect.getsource(
        __import__("app.domain.graph.langchain.agent_factory", fromlist=["create_bot_agent"]),
    )
    orchestrator_source = inspect.getsource(
        __import__("app.domain.graph.langchain.orchestrator_agent", fromlist=["run_tool_agent_turn"]),
    )
    assert "create_agent" in factory_source
    assert "from langchain.agents.factory import create_agent" in factory_source
    assert "run_tool_agent_turn" in orchestrator_source


def test_orchestrator_has_no_manual_tool_iteration_loop() -> None:
    source = inspect.getsource(
        __import__("app.domain.graph.orchestrator", fromlist=["OrchestratorRunner"]),
    )
    assert "MAX_TOOL_ITERATIONS" not in source
    assert "for _ in range" not in source


def test_workflows_use_langgraph_compiler() -> None:
    runner_source = inspect.getsource(
        __import__(
            "app.domain.workflow.workflow_graph_runner",
            fromlist=["WorkflowGraphRunner"],
        ),
    )
    compiler_source = inspect.getsource(
        __import__(
            "app.domain.workflow.workflow_graph_compiler",
            fromlist=["compile_workflow_graph"],
        ),
    )
    assert "compile_workflow_graph" in runner_source
    assert "StateGraph" in compiler_source


def test_chat_graph_uses_langgraph_router() -> None:
    chat_graph_source = inspect.getsource(
        __import__("app.domain.graph.chat_graph", fromlist=["ChatGraph"]),
    )
    router_source = inspect.getsource(
        __import__(
            "app.domain.graph.chat_router_compiler",
            fromlist=["compile_chat_router_graph"],
        ),
    )
    assert "compile_chat_router_graph" in chat_graph_source
    assert "StateGraph" in router_source
    assert "add_conditional_edges" in router_source


def test_chat_completion_uses_langsmith_parent_turn_tracing() -> None:
    source = inspect.getsource(
        __import__("app.services.chat_completion_service", fromlist=["ChatCompletionService"]),
    )
    assert "chat_turn_tracing" in source
    assert "turn_id=turn_id" in source or "turn_id=" in source


def test_no_legacy_pii_boundary_modules_in_app() -> None:
    assert not (APP_ROOT / "domain/pipeline/safety").exists()
    assert not (APP_ROOT / "domain/pipeline/sanitization").exists()
    assert not (APP_ROOT / "domain/pipeline/skills").exists()
    assert not (APP_ROOT / "domain/workflow/workflow_runner.py").exists()
    assert not (APP_ROOT / "domain/graph/langchain/sub_agent_agent.py").exists()
    app_py_files = list(APP_ROOT.rglob("*.py"))
    joined = "\n".join(path.read_text(encoding="utf-8") for path in app_py_files)
    assert "redact_pii" not in joined
    assert "SafetyPipeline" not in joined
    assert "from app.domain.workflow.workflow_runner" not in joined
