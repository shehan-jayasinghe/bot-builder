from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutorContext:
    executor: str
    connector: dict[str, Any]
    tool_config: dict[str, Any]
    args: dict[str, Any]
