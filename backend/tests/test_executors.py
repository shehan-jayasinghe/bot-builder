import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import StructuredTool

from app.domain.executors.context import ExecutorContext
from app.domain.executors.errors import ConnectorConfigError, MissingTemplateArgError, UnknownExecutorError
from app.domain.executors.langgraph_tools import build_langgraph_tool, build_tool_node, validate_tool_connector_pair
from app.domain.executors.registry import run_executor
from app.domain.executors.template import extract_placeholder_names, resolve_templates


def test_extract_placeholder_names() -> None:
    config = {
        "filter": {"customer_id": "{{customer_id}}"},
        "projection": ["name"],
    }
    assert extract_placeholder_names(config) == {"customer_id"}


def test_resolve_templates() -> None:
    config = {"filter": {"customer_id": "{{customer_id}}"}}
    resolved = resolve_templates(config, {"customer_id": "C-1"})
    assert resolved == {"filter": {"customer_id": "C-1"}}


def test_resolve_templates_missing_arg() -> None:
    with pytest.raises(MissingTemplateArgError):
        resolve_templates({"x": "{{missing}}"}, {})


def test_validate_tool_connector_pair_mismatch() -> None:
    tool = {"executor": "mongo_find_one"}
    connector = {"type": "http"}
    with pytest.raises(ConnectorConfigError):
        validate_tool_connector_pair(tool, connector)


def test_build_langgraph_tool_schema() -> None:
    tool = {
        "name": "customer_lookup",
        "description": "Find a customer",
        "executor": "mongo_find_one",
        "config": {
            "collection": "customers",
            "filter": {"customer_id": "{{customer_id}}"},
        },
    }
    connector = {
        "type": "mongo",
        "config": {"uri": "mongodb://localhost:27017", "database": "test"},
    }
    lg_tool = build_langgraph_tool(tool, connector)
    assert isinstance(lg_tool, StructuredTool)
    assert lg_tool.name == "customer_lookup"
    assert lg_tool.args_schema is not None
    assert "customer_id" in lg_tool.args_schema.model_fields


def test_run_executor_mongo_find_one() -> None:
    async def _run() -> None:
        ctx = ExecutorContext(
            executor="mongo_find_one",
            connector={
                "type": "mongo",
                "config": {"uri": "mongodb://localhost:27017", "database": "shop"},
            },
            tool_config={
                "collection": "customers",
                "filter": {"customer_id": "{{customer_id}}"},
            },
            args={"customer_id": "C-99"},
        )

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value={"customer_id": "C-99", "name": "Ada"})
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        with patch("app.domain.executors.mongo_ops.org_mongo_db") as mock_ctx:
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await run_executor(ctx)

        assert result == {"customer_id": "C-99", "name": "Ada"}
        mock_collection.find_one.assert_awaited_once_with({"customer_id": "C-99"})

    asyncio.run(_run())


def test_run_executor_unknown() -> None:
    async def _run() -> None:
        ctx = ExecutorContext(
            executor="not_real",
            connector={"type": "mongo", "config": {}},
            tool_config={},
            args={},
        )
        with pytest.raises(UnknownExecutorError):
            await run_executor(ctx)

    asyncio.run(_run())


def test_langgraph_tool_invocation() -> None:
    async def _run() -> None:
        tool_doc = {
            "name": "ping_api",
            "description": "Ping API",
            "executor": "http_request",
            "config": {"method": "GET", "path": "/health"},
        }
        connector = {
            "type": "http",
            "config": {"base_url": "https://api.example.com", "auth_type": "none"},
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"ok": True}

        with patch("app.domain.executors.http_ops.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.request = AsyncMock(return_value=mock_response)
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client_cls.return_value = client

            lg_tool = build_langgraph_tool(tool_doc, connector)
            raw = await lg_tool.ainvoke({})
            result = json.loads(raw)
            assert result["status_code"] == 200
            assert result["body"] == {"ok": True}

    asyncio.run(_run())


def test_build_tool_node() -> None:
    tool = {
        "name": "list_items",
        "description": "List items",
        "executor": "mongo_find_many",
        "config": {"collection": "items", "filter": {}},
    }
    connector = {
        "type": "mongo",
        "config": {"uri": "mongodb://localhost:27017", "database": "test"},
    }
    node = build_tool_node([(tool, connector)])
    assert node.tools_by_name["list_items"].name == "list_items"
