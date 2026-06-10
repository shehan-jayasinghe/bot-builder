from app.shared.exceptions.base import CoreError


class AssistantLoadError(CoreError):
    """Base error when assistant configuration cannot be loaded."""


class ChannelNotFoundError(AssistantLoadError):
    """No active channel exists for the given webhook_id."""


class AgentNotFoundError(AssistantLoadError):
    """No published agent exists for the channel's agent_id."""
