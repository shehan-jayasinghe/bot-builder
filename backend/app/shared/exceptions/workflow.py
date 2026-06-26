from app.shared.exceptions.base import CoreError


class WorkflowError(CoreError):
    """Base error for workflow API operations."""


class WorkflowLimitReachedError(WorkflowError):
    """Organization has reached the maximum number of workflows."""
