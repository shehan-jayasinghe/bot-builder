from app.shared.exceptions.base import CoreError


class EvaluationError(CoreError):
    """Base error for RAG evaluation API."""


class EvaluationDisabledError(EvaluationError):
    """RAG evaluation feature flag is off."""


class EvalRunNotFoundError(EvaluationError):
    """Evaluation run does not exist for the agent."""
