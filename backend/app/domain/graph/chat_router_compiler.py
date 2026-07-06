from __future__ import annotations

from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph


class ChatRouterState(TypedDict, total=False):
    finished: bool
    needs_workflow_enter: bool
    result: Any


class ChatRouterEngine(Protocol):
    async def run_active_workflow_path(self) -> ChatRouterState: ...

    async def run_sticky_sub_agent_path(self) -> ChatRouterState: ...

    async def run_orchestrator_path(self) -> ChatRouterState: ...

    async def run_workflow_enter_path(self) -> ChatRouterState: ...

    def route_session(self) -> str: ...


def compile_chat_router_graph(engine: ChatRouterEngine) -> Any:
    """Compile session-level chat router: workflow → sticky sub-agent → orchestrator."""

    async def active_workflow_node(_state: ChatRouterState) -> ChatRouterState:
        return await engine.run_active_workflow_path()

    async def sticky_sub_agent_node(_state: ChatRouterState) -> ChatRouterState:
        return await engine.run_sticky_sub_agent_path()

    async def orchestrator_node(_state: ChatRouterState) -> ChatRouterState:
        return await engine.run_orchestrator_path()

    async def workflow_enter_node(_state: ChatRouterState) -> ChatRouterState:
        return await engine.run_workflow_enter_path()

    def route_from_session(_state: ChatRouterState) -> str:
        route = engine.route_session()
        if route == "active_workflow":
            return "active_workflow"
        if route == "sticky_sub_agent":
            return "sticky_sub_agent"
        return "orchestrator"

    def after_sticky(state: ChatRouterState) -> str:
        if state.get("finished"):
            return END
        return "orchestrator"

    def after_orchestrator(state: ChatRouterState) -> str:
        if state.get("needs_workflow_enter"):
            return "workflow_enter"
        return END

    graph = StateGraph(ChatRouterState)
    graph.add_node("active_workflow", active_workflow_node)
    graph.add_node("sticky_sub_agent", sticky_sub_agent_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("workflow_enter", workflow_enter_node)

    graph.add_conditional_edges(
        START,
        route_from_session,
        {
            "active_workflow": "active_workflow",
            "sticky_sub_agent": "sticky_sub_agent",
            "orchestrator": "orchestrator",
        },
    )
    graph.add_edge("active_workflow", END)
    graph.add_conditional_edges(
        "sticky_sub_agent",
        after_sticky,
        {"orchestrator": "orchestrator", END: END},
    )
    graph.add_conditional_edges(
        "orchestrator",
        after_orchestrator,
        {"workflow_enter": "workflow_enter", END: END},
    )
    graph.add_edge("workflow_enter", END)

    return graph.compile()
