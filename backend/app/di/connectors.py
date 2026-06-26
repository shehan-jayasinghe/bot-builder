from fastapi import Depends

from app.di.repositories import get_connector_repository
from app.infrastructure.db.repositories.mongo.connector_repository import ConnectorRepository
from app.services.connector_service import ConnectorService


def get_connector_service(
    connector_repository: ConnectorRepository = Depends(get_connector_repository),
) -> ConnectorService:
    return ConnectorService(connector_repository=connector_repository)
