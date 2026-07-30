from pathlib import Path

from app.config import settings


def kb_index_root(*, organization_id: str, knowledgebase_id: str) -> Path:
    return Path(settings.rag_index_dir) / organization_id / knowledgebase_id


def graph_index_marker(*, organization_id: str, knowledgebase_id: str) -> Path:
    return kb_index_root(
        organization_id=organization_id,
        knowledgebase_id=knowledgebase_id,
    ) / "graph.ready"
