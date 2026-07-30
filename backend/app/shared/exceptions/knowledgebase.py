from app.shared.exceptions.base import CoreError


class KnowledgebaseError(CoreError):
    """Base error for knowledge base API operations."""


class KnowledgebaseNotFoundError(KnowledgebaseError):
    """Knowledge base does not exist or is not accessible for the organization."""
