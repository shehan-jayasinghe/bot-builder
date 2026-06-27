from dataclasses import dataclass, field


@dataclass(frozen=True)
class RagRetrieveResult:
    context: str
    chunk_count: int = 0
    kb_ids: list[str] = field(default_factory=list)
    storage_types: list[str] = field(default_factory=list)
    error: str | None = None
