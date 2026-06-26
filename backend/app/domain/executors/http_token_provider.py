import logging
import time
from hashlib import sha256
from typing import Any

import httpx

from app.domain.executors.errors import ConnectorConfigError

logger = logging.getLogger(__name__)

_TOKEN_TIMEOUT = 30.0
_CACHE_SKEW_SECONDS = 30
_MIN_CACHE_SECONDS = 60

_token_cache: dict[str, tuple[str, float]] = {}


def _cache_key(config: dict[str, Any]) -> str:
    material = "|".join(
        [
            str(config.get("token_url", "")),
            str(config.get("client_id", "")),
            str(config.get("scope", "")),
            str(config.get("grant_type", "client_credentials")),
        ]
    )
    return sha256(material.encode()).hexdigest()


def clear_oauth_token_cache() -> None:
    _token_cache.clear()


async def fetch_oauth2_client_credentials_token(config: dict[str, Any]) -> str:
    token_url = config.get("token_url")
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    if not token_url or not client_id or not client_secret:
        raise ConnectorConfigError(
            "OAuth2 client credentials requires token_url, client_id, and client_secret"
        )

    cache_key = _cache_key(config)
    cached = _token_cache.get(cache_key)
    if cached is not None and cached[1] > time.time():
        return cached[0]

    grant_type = str(config.get("grant_type") or "client_credentials")
    form_data: dict[str, str] = {
        "grant_type": grant_type,
        "client_id": str(client_id),
        "client_secret": str(client_secret),
    }
    scope = config.get("scope")
    if scope:
        form_data["scope"] = str(scope)

    async with httpx.AsyncClient(timeout=_TOKEN_TIMEOUT) as client:
        response = await client.post(
            str(token_url),
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code >= 400:
        logger.warning("OAuth2 token request failed with status %s", response.status_code)
        raise ConnectorConfigError(
            f"OAuth2 token request failed with status {response.status_code}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise ConnectorConfigError("OAuth2 token response was not valid JSON") from exc

    access_token = payload.get("access_token")
    if not access_token:
        raise ConnectorConfigError("OAuth2 token response missing access_token")

    expires_in = int(payload.get("expires_in", _MIN_CACHE_SECONDS))
    ttl = max(expires_in - _CACHE_SKEW_SECONDS, _MIN_CACHE_SECONDS)
    _token_cache[cache_key] = (str(access_token), time.time() + ttl)
    return str(access_token)
