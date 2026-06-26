from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.domain.executors.context import ExecutorContext
from app.domain.executors.errors import ConnectorConfigError
from app.domain.executors.serialize import to_jsonable
from app.domain.executors.template import resolve_templates


def _mongo_connector_config(connector: dict[str, Any]) -> tuple[str, str]:
    config = connector.get("config") or {}
    uri = config.get("uri")
    database = config.get("database")
    if not uri or not database:
        raise ConnectorConfigError("Mongo connector requires config.uri and config.database")
    return uri, database


@asynccontextmanager
async def org_mongo_db(connector: dict[str, Any]) -> AsyncIterator[AsyncIOMotorDatabase]:
    uri, database = _mongo_connector_config(connector)
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
    try:
        yield client[database]
    finally:
        client.close()


def _resolved_config(ctx: ExecutorContext) -> dict[str, Any]:
    return resolve_templates(ctx.tool_config, ctx.args)


async def mongo_find_one(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    filter_doc = config["filter"]
    projection = config.get("projection")

    async with org_mongo_db(ctx.connector) as db:
        kwargs: dict[str, Any] = {}
        if projection is not None:
            kwargs["projection"] = {field: 1 for field in projection}
        doc = await db[collection].find_one(filter_doc, **kwargs)
        return to_jsonable(doc)


async def mongo_find_many(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    filter_doc = config["filter"]
    projection = config.get("projection")
    sort = config.get("sort")
    limit = min(int(config.get("limit", 100)), 1000)

    async with org_mongo_db(ctx.connector) as db:
        cursor = db[collection].find(filter_doc)
        if projection is not None:
            cursor = cursor.projection({field: 1 for field in projection})
        if sort:
            cursor = cursor.sort(list(sort.items()))
        cursor = cursor.limit(limit)
        docs = await cursor.to_list(length=limit)
        return to_jsonable(docs)


async def mongo_insert(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    document = config["document"]

    async with org_mongo_db(ctx.connector) as db:
        result = await db[collection].insert_one(document)
        return {"inserted_id": str(result.inserted_id)}


async def mongo_update(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    filter_doc = config["filter"]
    update_doc = config["update"]

    async with org_mongo_db(ctx.connector) as db:
        result = await db[collection].update_one(filter_doc, update_doc)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }


async def mongo_delete(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    filter_doc = config["filter"]

    async with org_mongo_db(ctx.connector) as db:
        result = await db[collection].delete_one(filter_doc)
        return {"deleted_count": result.deleted_count}


async def mongo_aggregate(ctx: ExecutorContext) -> Any:
    config = _resolved_config(ctx)
    collection = config["collection"]
    pipeline = config["pipeline"]

    async with org_mongo_db(ctx.connector) as db:
        cursor = db[collection].aggregate(pipeline)
        docs = await cursor.to_list(length=1000)
        return to_jsonable(docs)
