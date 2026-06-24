from app.shared.exceptions.base import CoreError


class AgentError(CoreError):
    """Base error for agent API operations."""


class AgentNotFoundError(AgentError):
    """Agent does not exist or is not accessible for the caller's organization."""
