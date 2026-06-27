import asyncio
import logging
from typing import Any

from app.domain.constants.knowledgebase_constants import (
    STORAGE_TYPE_GRAPH,
    STORAGE_TYPE_KEYWORD,
    STORAGE_TYPE_VECTOR,
)
from app.domain.models.runtime_bundle import RuntimeKnowledgeBase
from app.domain.pipeline.rag.keyword_search import KeywordSearch
from app.domain.pipeline.rag.rag_result import RagRetrieveResult
from app.domain.pipeline.rag.vector_search import VectorSearch

logger = logging.getLogger(__name__)


def format_rag_context(grouped_chunks: dict[str, list[str]]) -> str:
    if not grouped_chunks:
        return ""

    sections: list[str] = []
    for kb_name, chunks in grouped_chunks.items():
        lines = "\n".join(f"- {chunk}" for chunk in chunks if chunk.strip())
        if lines:
            sections.append(f"### {kb_name}\n{lines}")
    return "\n\n".join(sections)


class RAGRetriever:
    def __init__(
        self,
        *,
        vector_search: VectorSearch | None = None,
        keyword_search: KeywordSearch | None = None,
    ) -> None:
        self._vector_search = vector_search or VectorSearch()
        self._keyword_search = keyword_search or KeywordSearch()

    async def retrieve(
        self,
        *,
        query: str,
        knowledge_bases: list[RuntimeKnowledgeBase],
        organization_id: str,
    ) -> RagRetrieveResult:
        if not knowledge_bases:
            return RagRetrieveResult(context="")

        if not query.strip():
            return RagRetrieveResult(context="")

        grouped: dict[str, list[str]] = {}
        seen_texts: set[str] = set()
        chunk_count = 0
        kb_ids: list[str] = []
        storage_types: list[str] = []
        errors: list[str] = []

        for kb in knowledge_bases:
            kb_ids.append(kb.id)
            if kb.storage_type not in storage_types:
                storage_types.append(kb.storage_type)

            try:
                hits = await self._search_kb(
                    kb=kb,
                    query=query,
                    organization_id=organization_id,
                )
            except Exception as exc:
                logger.exception(
                    "RAG retrieval failed for knowledge_base_id=%s storage_type=%s",
                    kb.id,
                    kb.storage_type,
                )
                errors.append(f"{kb.id}: {exc}")
                continue

            kb_chunks: list[str] = []
            for hit in hits:
                text = hit["text"]
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                kb_chunks.append(text)
                chunk_count += 1

            if kb_chunks:
                grouped[kb.name] = kb_chunks

        context = format_rag_context(grouped)
        error = "; ".join(errors) if errors else None
        return RagRetrieveResult(
            context=context,
            chunk_count=chunk_count,
            kb_ids=kb_ids,
            storage_types=storage_types,
            error=error,
        )

    async def _search_kb(
        self,
        *,
        kb: RuntimeKnowledgeBase,
        query: str,
        organization_id: str,
    ) -> list[dict[str, Any]]:
        if kb.storage_type == STORAGE_TYPE_VECTOR:
            hits = await asyncio.to_thread(
                self._vector_search.search,
                organization_id=organization_id,
                knowledgebase_id=kb.id,
                query=query,
            )
            return [
                {"text": hit.text, "score": hit.score, "chunk_id": hit.chunk_id}
                for hit in hits
            ]

        if kb.storage_type == STORAGE_TYPE_KEYWORD:
            hits = await asyncio.to_thread(
                self._keyword_search.search,
                organization_id=organization_id,
                knowledgebase_id=kb.id,
                query=query,
            )
            return [
                {"text": hit.text, "score": hit.score, "chunk_id": hit.chunk_id}
                for hit in hits
            ]

        if kb.storage_type == STORAGE_TYPE_GRAPH:
            logger.info("Graph RAG not implemented for knowledge_base_id=%s", kb.id)
            return []

        logger.warning("Unsupported storage_type=%s for knowledge_base_id=%s", kb.storage_type, kb.id)
        return []
