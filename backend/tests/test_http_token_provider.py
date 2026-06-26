import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.executors.errors import ConnectorConfigError
from app.domain.executors.http_token_provider import clear_oauth_token_cache, fetch_oauth2_client_credentials_token


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_oauth_token_cache()


def test_fetch_oauth2_client_credentials_token() -> None:
    async def _run() -> None:
        config = {
            "token_url": "https://auth.example.com/token",
            "client_id": "app-client",
            "client_secret": "super-secret",
            "grant_type": "client_credentials",
            "scope": "read",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "abc123", "expires_in": 300}

        with patch("app.domain.executors.http_token_provider.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.post = AsyncMock(return_value=mock_response)
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client_cls.return_value = client

            token = await fetch_oauth2_client_credentials_token(config)
            assert token == "abc123"

            cached = await fetch_oauth2_client_credentials_token(config)
            assert cached == "abc123"
            assert client.post.await_count == 1

    asyncio.run(_run())


def test_fetch_oauth2_client_credentials_token_missing_fields() -> None:
    async def _run() -> None:
        with pytest.raises(ConnectorConfigError):
            await fetch_oauth2_client_credentials_token(
                {
                    "token_url": "https://auth.example.com/token",
                    "client_id": "app-client",
                }
            )

    asyncio.run(_run())
