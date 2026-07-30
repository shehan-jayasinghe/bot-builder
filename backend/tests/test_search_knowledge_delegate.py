import asyncio
from unittest.mock import AsyncMock

from app.domain.graph.search_knowledge_delegate import (
    SEARCH_KNOWLEDGE_TOOL_NAME,
    build_search_knowledge_tool,
    execute_search_knowledge,
    scope_knowledge_bases,
)
from app.domain.models.capability_catalog import CapabilityCatalog, CapabilityEntry
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.rag_result import RagRetrieveResult


def test_build_search_knowledge_tool_returns_none_when_no_kbs() -> None:
    assert build_search_knowledge_tool([], capability_catalog=None) is None


def test_build_search_knowledge_tool_includes_routing_hint() -> None:
    kb = RuntimeKnowledgeBase(
        id="kb-1",
        name="FAQ",
        description="Frequently asked questions",
        storage_type="vector",
        status="active",
    )
    catalog = CapabilityCatalog(
        knowledge_bases={"kb-1": CapabilityEntry(routing_hint="Use for product policy questions")},
    )

    tool = build_search_knowledge_tool([kb], capability_catalog=catalog)

    assert tool is not None
    assert tool.name == SEARCH_KNOWLEDGE_TOOL_NAME
    assert "product policy questions" in tool.description
    assert "FAQ" in tool.description


def test_scope_knowledge_bases_filters_by_name() -> None:
    kbs = [
        RuntimeKnowledgeBase(id="1", name="FAQ", storage_type="vector", status="active"),
        RuntimeKnowledgeBase(id="2", name="Policies", storage_type="vector", status="active"),
    ]

    scoped = scope_knowledge_bases(kbs, ["Policies"])

    assert len(scoped) == 1
    assert scoped[0].name == "Policies"


def test_execute_search_knowledge_delegates_to_retriever() -> None:
    async def _run() -> None:
        kb = RuntimeKnowledgeBase(id="kb-1", name="FAQ", storage_type="vector", status="active")
        rag = AsyncMock()
        rag.retrieve.return_value = RagRetrieveResult(
            context="### FAQ\n- answer",
            kb_ids=["kb-1"],
            chunk_count=1,
        )

        result = await execute_search_knowledge(
            rag=rag,
            query="refund policy",
            knowledge_bases=[kb],
            organization_id="org-1",
        )

        assert result.context == "### FAQ\n- answer"
        rag.retrieve.assert_awaited_once_with(
            query="refund policy",
            knowledge_bases=[kb],
            organization_id="org-1",
        )

    asyncio.run(_run())
