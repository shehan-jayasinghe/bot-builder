import re
from typing import Any


def validate_slot_value(
    value: str,
    *,
    validation: dict[str, Any] | None = None,
    input_mode: str | None = None,
    options: list[Any] | None = None,
    required: bool = True,
) -> tuple[bool, str | None]:
    stripped = value.strip()
    if not stripped:
        if required:
            return False, "Value is required"
        return True, None

    if input_mode == "multiselect" and options:
        allowed = _normalized_options(options)
        if allowed and stripped not in allowed:
            return False, "Please choose from the available options"

    if not validation:
        return True, None

    val_type = str(validation.get("type", "string"))
    pattern = validation.get("pattern")

    if val_type == "number":
        try:
            float(stripped)
        except ValueError:
            return False, "Invalid number"
    elif val_type == "integer":
        try:
            int(stripped)
        except ValueError:
            return False, "Invalid integer"
    elif val_type == "boolean":
        if stripped.lower() not in {"true", "false", "yes", "no", "1", "0"}:
            return False, "Invalid boolean"
    elif val_type == "email":
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", stripped):
            return False, "Invalid email"

    if pattern and not re.fullmatch(str(pattern), stripped):
        return False, "Invalid format"

    return True, None


def _normalized_options(options: list[Any]) -> list[str]:
    result: list[str] = []
    for option in options:
        if isinstance(option, dict):
            for key in ("value", "label", "title", "payload"):
                raw = option.get(key)
                if raw:
                    result.append(str(raw))
                    break
        elif option is not None:
            result.append(str(option))
    return [item for item in result if item]
