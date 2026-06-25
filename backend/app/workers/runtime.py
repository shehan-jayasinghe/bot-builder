import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

from app.infrastructure.db.mongo import connect_mongo, disconnect_mongo

T = TypeVar("T")


def run_async_task(coro: Coroutine[Any, Any, T]) -> T:
    async def _runner() -> T:
        await connect_mongo()
        try:
            return await coro
        finally:
            await disconnect_mongo()

    return asyncio.run(_runner())
