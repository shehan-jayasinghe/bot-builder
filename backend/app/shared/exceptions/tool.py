from app.shared.exceptions.base import CoreError


class ToolError(CoreError):
    """Base error for tool API operations."""


class ToolNotFoundError(ToolError):
    """Tool does not exist or is not accessible for the agent/org."""


class ToolNameExistsError(ToolError):
    """Tool name already exists for the agent."""


class ToolConnectorTypeMismatchError(ToolError):
    """Connector type does not match executor requirements."""
