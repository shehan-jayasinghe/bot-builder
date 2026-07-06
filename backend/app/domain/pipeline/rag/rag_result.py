from dataclasses import dataclass, field


@dataclass(frozen=True)
class RagChunk:
    text: str
    rank: int
    kb_id: str
    kb_name: str
    score: float | None = None
    chunk_id: str | None = None


@dataclass(frozen=True)
class RagRetrieveResult:
    context: str
    chunk_count: int = 0
    kb_ids: list[str] = field(default_factory=list)
    storage_types: list[str] = field(default_factory=list)
    chunks: list[RagChunk] = field(default_factory=list)
    error: str | None = None
