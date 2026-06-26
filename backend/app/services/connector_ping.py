import logging
from typing import Any

import httpx

from app.domain.executors.mongo_ops import org_mongo_db
from app.domain.executors.http_ops import _build_auth, _build_headers
from app.schemas.connector import ConnectorType
from app.shared.exceptions.connector import ConnectionTestFailedError

logger = logging.getLogger(__name__)

_PING_TIMEOUT = 5.0


async def test_connector_connection(connector_type: str, config: dict[str, Any]) -> None:
    try:
        if connector_type == ConnectorType.MONGO:
            async with org_mongo_db({"config": config}) as db:
                await db.command("ping")
            return

        if connector_type == ConnectorType.HTTP:
            base_url = str(config["base_url"]).rstrip("/")
            auth = _build_auth(config)
            headers = _build_headers(config, None)
            async with httpx.AsyncClient(timeout=_PING_TIMEOUT, auth=auth) as client:
                response = await client.get(base_url, headers=headers)
            if response.status_code >= 500:
                raise ConnectionTestFailedError(
                    f"HTTP connection test failed with status {response.status_code}"
                )
            return

        raise ConnectionTestFailedError(f"Unsupported connector type: {connector_type}")
    except ConnectionTestFailedError:
        raise
    except Exception as exc:
        logger.warning("Connector ping failed: %s", exc)
        raise ConnectionTestFailedError(f"Connection test failed: {exc}") from exc
