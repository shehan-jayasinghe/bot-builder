from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.domain.models.capability_catalog import CapabilityCatalog, get_routing_hint
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.rag_result import RagRetrieveResult
from app.domain.pipeline.rag.retriever import RAGRetriever

SEARCH_KNOWLEDGE_TOOL_NAME = "search_knowledge"


class _SearchKnowledgeArgs(BaseModel):
    query: str = Field(description="Search query to find relevant knowledge base content")
    knowledge_base_names: list[str] | None = Field(
        default=None,
        description="Optional list of knowledge base names to narrow the search scope",
    )


def scope_knowledge_bases(
    knowledge_bases: list[RuntimeKnowledgeBase],
    knowledge_base_names: list[str] | None,
) -> list[RuntimeKnowledgeBase]:
    if not knowledge_base_names:
        return list(knowledge_bases)
    name_set = {name.strip().lower() for name in knowledge_base_names if name and name.strip()}
    if not name_set:
        return list(knowledge_bases)
    return [kb for kb in knowledge_bases if kb.name.strip().lower() in name_set]


def _build_search_description(
    knowledge_bases: list[RuntimeKnowledgeBase],
    *,
    capability_catalog: CapabilityCatalog | None,
) -> str:
    lines = [
        "Search attached knowledge bases for information relevant to the user's question.",
        "Call this when catalog routing hints or the conversation require factual context from knowledge bases.",
    ]
    for kb in knowledge_bases:
        hint = (
            get_routing_hint(capability_catalog, "knowledge_bases", kb.id)
            if capability_catalog is not None
            else None
        )
        label = kb.description or kb.name
        if hint:
            lines.append(f"- {kb.name}: {hint} — {label}")
        else:
            lines.append(f"- {kb.name}: {label}")
    return "\n".join(lines)


def build_search_knowledge_tool(
    knowledge_bases: list[RuntimeKnowledgeBase],
    *,
    capability_catalog: CapabilityCatalog | None,
) -> StructuredTool | None:
    if not knowledge_bases:
        return None

    async def _search_stub(**_kwargs: Any) -> str:
        return "Knowledge search is handled by the chat runtime."

    return StructuredTool.from_function(
        coroutine=_search_stub,
        name=SEARCH_KNOWLEDGE_TOOL_NAME,
        description=_build_search_description(
            knowledge_bases,
            capability_catalog=capability_catalog,
        ),
        args_schema=_SearchKnowledgeArgs,
    )


async def execute_search_knowledge(
    *,
    rag: RAGRetriever,
    query: str,
    knowledge_bases: list[RuntimeKnowledgeBase],
    organization_id: str,
    knowledge_base_names: list[str] | None = None,
) -> RagRetrieveResult:
    scoped = scope_knowledge_bases(knowledge_bases, knowledge_base_names)
    return await rag.retrieve(
        query=query,
        knowledge_bases=scoped,
        organization_id=organization_id,
    )
