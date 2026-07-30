from app.shared.exceptions.base import CoreError


class ConnectorError(CoreError):
    """Base error for connector API operations."""


class ConnectorNotFoundError(ConnectorError):
    """Connector does not exist or is not accessible for the caller's organization."""


class ConnectorNameExistsError(ConnectorError):
    """Connector name already exists for the organization."""


class ConnectionTestFailedError(ConnectorError):
    """Optional connection test failed before save."""
