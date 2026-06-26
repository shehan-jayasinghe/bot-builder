from typing import Any

import httpx

from app.domain.executors.context import ExecutorContext
from app.domain.executors.errors import ConnectorConfigError
from app.domain.executors.template import resolve_templates

_DEFAULT_TIMEOUT = 30.0


def _http_connector_config(connector: dict[str, Any]) -> dict[str, Any]:
    config = connector.get("config") or {}
    base_url = config.get("base_url")
    if not base_url:
        raise ConnectorConfigError("HTTP connector requires config.base_url")
    return config


def _build_auth(config: dict[str, Any]) -> httpx.Auth | None:
    auth_type = (config.get("auth_type") or "none").lower()
    if auth_type == "bearer":
        token = config.get("auth_token")
        if not token:
            raise ConnectorConfigError("HTTP bearer auth requires auth_token")
        return httpx.BearerToken(token)
    if auth_type == "basic":
        username = config.get("auth_username")
        password = config.get("auth_password")
        if not username or password is None:
            raise ConnectorConfigError("HTTP basic auth requires auth_username and auth_password")
        return httpx.BasicAuth(username, password)
    return None


def _build_headers(connector_config: dict[str, Any], tool_headers: dict[str, Any] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    default_headers = connector_config.get("default_headers") or {}
    headers.update({str(k): str(v) for k, v in default_headers.items()})
    if tool_headers:
        headers.update({str(k): str(v) for k, v in tool_headers.items()})

    auth_type = (connector_config.get("auth_type") or "none").lower()
    if auth_type == "api_key":
        header_name = connector_config.get("api_key_header") or "X-API-Key"
        token = connector_config.get("auth_token")
        if not token:
            raise ConnectorConfigError("HTTP api_key auth requires auth_token")
        headers[header_name] = str(token)
    return headers


async def http_request(ctx: ExecutorContext) -> Any:
    connector_config = _http_connector_config(ctx.connector)
    config = resolve_templates(ctx.tool_config, ctx.args)

    base_url = connector_config["base_url"].rstrip("/")
    path = str(config["path"]).lstrip("/")
    url = f"{base_url}/{path}"
    method = str(config["method"]).upper()
    headers = _build_headers(connector_config, config.get("headers"))
    query = config.get("query")
    body = config.get("body")

    auth = _build_auth(connector_config)

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT, auth=auth) as client:
        response = await client.request(
            method,
            url,
            headers=headers,
            params=query,
            json=body,
        )

    result: dict[str, Any] = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
    }
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            result["body"] = response.json()
        except ValueError:
            result["body"] = response.text
    else:
        result["body"] = response.text
    return result
