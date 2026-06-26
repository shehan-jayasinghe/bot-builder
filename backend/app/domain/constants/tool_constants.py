from enum import StrEnum


class ToolStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


TOOL_STATUS_ACTIVE = ToolStatus.ACTIVE.value
