import re
from datetime import UTC, datetime
from typing import Any

from app.domain.executors.errors import MissingTemplateArgError

_PLACEHOLDER = re.compile(r"^\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}$")
_RUNTIME_VARS = {
    "_now_iso": lambda: datetime.now(UTC).isoformat(),
}


def extract_placeholder_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, str):
        match = _PLACEHOLDER.match(value.strip())
        if match:
            name = match.group(1)
            if name not in _RUNTIME_VARS:
                names.add(name)
    elif isinstance(value, dict):
        for item in value.values():
            names.update(extract_placeholder_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(extract_placeholder_names(item))
    return names


def resolve_templates(value: Any, args: dict[str, Any]) -> Any:
    if isinstance(value, str):
        match = _PLACEHOLDER.match(value.strip())
        if not match:
            return value
        key = match.group(1)
        if key in _RUNTIME_VARS:
            return _RUNTIME_VARS[key]()
        if key not in args:
            raise MissingTemplateArgError(key)
        return args[key]
    if isinstance(value, dict):
        return {k: resolve_templates(v, args) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_templates(item, args) for item in value]
    return value
