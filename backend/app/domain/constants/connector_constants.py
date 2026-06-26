from enum import StrEnum


class ConnectorType(StrEnum):
    MONGO = "mongo"
    HTTP = "http"


class ConnectorStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


MVP_CONNECTOR_TYPES: frozenset[str] = frozenset(ConnectorType)

CONNECTOR_STATUS_ACTIVE = ConnectorStatus.ACTIVE.value
