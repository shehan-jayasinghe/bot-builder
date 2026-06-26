import re
from typing import Any

_SECRET_KEYS = frozenset({"auth_token", "auth_password", "client_secret", "uri"})


def mask_mongo_uri(uri: str) -> str:
    return re.sub(r"(mongodb(?:\+srv)?://[^:]+:)([^@]+)(@)", r"\1***\3", uri)


def mask_connector_config(connector_type: str, config: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in config.items():
        if key in _SECRET_KEYS:
            if key == "uri" and connector_type == "mongo":
                masked[key] = mask_mongo_uri(str(value))
            else:
                masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = value
        else:
            masked[key] = value
    return masked
