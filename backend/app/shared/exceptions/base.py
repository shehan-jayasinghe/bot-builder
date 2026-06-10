class BotBuilderError(Exception):
    """Base error for bot-builder."""


class CoreError(BotBuilderError):
    """Errors raised from core/domain logic."""
