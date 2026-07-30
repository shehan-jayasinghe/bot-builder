import pytest

from app.services.connector_masking import mask_connector_config, mask_mongo_uri
from app.schemas.connector import (
    ConnectorType,
    HttpConnectorConfig,
    MongoConnectorConfig,
    parse_connector_config,
)


def test_mask_mongo_uri() -> None:
    uri = "mongodb+srv://user:secret@cluster.example.net"
    assert mask_mongo_uri(uri) == "mongodb+srv://user:***@cluster.example.net"


def test_mask_connector_config_http() -> None:
    config = {
        "base_url": "https://api.example.com",
        "auth_type": "bearer",
        "auth_token": "sk_live_secret",
    }
    masked = mask_connector_config("http", config)
    assert masked["auth_token"] == "***"
    assert masked["base_url"] == "https://api.example.com"


def test_parse_mongo_config() -> None:
    parsed = parse_connector_config(
        ConnectorType.MONGO,
        {"uri": "mongodb://localhost:27017", "database": "test"},
    )
    assert parsed == MongoConnectorConfig(
        uri="mongodb://localhost:27017",
        database="test",
    ).model_dump()


def test_parse_http_config_requires_bearer_token() -> None:
    with pytest.raises(ValueError):
        parse_connector_config(
            ConnectorType.HTTP,
            {"base_url": "https://api.example.com", "auth_type": "bearer"},
        )


def test_parse_http_config() -> None:
    parsed = parse_connector_config(
        ConnectorType.HTTP,
        {
            "base_url": "https://api.example.com",
            "auth_type": "none",
        },
    )
    assert parsed["base_url"] == "https://api.example.com"


def test_parse_http_config_oauth2_client_credentials() -> None:
    parsed = parse_connector_config(
        ConnectorType.HTTP,
        {
            "base_url": "https://api.example.com",
            "auth_type": "oauth2_client_credentials",
            "token_url": "https://auth.example.com/token",
            "client_id": "app-client",
            "client_secret": "super-secret",
            "grant_type": "client_credentials",
            "scope": "read write",
        },
    )
    assert parsed["auth_type"] == "oauth2_client_credentials"
    assert parsed["token_url"] == "https://auth.example.com/token"
    assert parsed["client_id"] == "app-client"


def test_parse_http_config_oauth2_requires_secret_fields() -> None:
    with pytest.raises(ValueError):
        parse_connector_config(
            ConnectorType.HTTP,
            {
                "base_url": "https://api.example.com",
                "auth_type": "oauth2_client_credentials",
                "token_url": "https://auth.example.com/token",
                "client_id": "app-client",
            },
        )


def test_mask_connector_config_oauth2() -> None:
    config = {
        "base_url": "https://api.example.com",
        "auth_type": "oauth2_client_credentials",
        "token_url": "https://auth.example.com/token",
        "client_id": "app-client",
        "client_secret": "super-secret",
    }
    masked = mask_connector_config("http", config)
    assert masked["client_secret"] == "***"
    assert masked["client_id"] == "app-client"
