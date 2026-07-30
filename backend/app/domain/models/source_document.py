from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceDocument:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkDocument:
    chunk_id: str
    text: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
