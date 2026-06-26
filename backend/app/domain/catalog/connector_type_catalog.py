from typing import Any

from app.domain.constants.connector_constants import ConnectorType


def get_connector_type_catalog() -> list[dict[str, Any]]:
    return [
        {
            "type": ConnectorType.MONGO,
            "label": "MongoDB",
            "description": "Connect to a MongoDB database for read/write tools.",
            "mvp": True,
            "config_schema": {
                "uri": {"type": "string", "required": True, "secret": True},
                "database": {"type": "string", "required": True, "secret": False},
            },
            "compatible_executors": [
                "mongo_find_one",
                "mongo_find_many",
                "mongo_insert",
                "mongo_update",
                "mongo_delete",
                "mongo_aggregate",
            ],
        },
        {
            "type": ConnectorType.HTTP,
            "label": "REST / HTTP",
            "description": "Connect to a REST API with optional authentication.",
            "mvp": True,
            "config_schema": {
                "base_url": {"type": "string", "required": True, "secret": False},
                "auth_type": {
                    "type": "enum",
                    "values": ["none", "bearer", "basic", "api_key"],
                    "required": False,
                },
                "auth_token": {"type": "string", "required": False, "secret": True},
                "auth_username": {"type": "string", "required": False, "secret": False},
                "auth_password": {"type": "string", "required": False, "secret": True},
                "api_key_header": {"type": "string", "required": False, "secret": False},
                "default_headers": {"type": "object", "required": False, "secret": False},
            },
            "compatible_executors": ["http_request"],
        },
    ]
