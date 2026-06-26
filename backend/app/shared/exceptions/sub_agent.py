from app.shared.exceptions.base import CoreError


class SubAgentError(CoreError):
    """Base error for sub-agent API operations."""


class SubAgentNotFoundError(SubAgentError):
    """Sub-agent does not exist or is not accessible for the agent/org."""


class SubAgentNameExistsError(SubAgentError):
    """Sub-agent name already exists for the parent agent."""


class SubAgentLimitReachedError(SubAgentError):
    """Parent agent sub-agent limit reached."""


class SubAgentInvalidCapabilityError(SubAgentError):
    """Tool, knowledge base, or workflow is not attached to the parent agent."""
