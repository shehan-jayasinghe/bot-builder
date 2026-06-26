from collections.abc import Awaitable, Callable
from typing import Any

from app.domain.constants.executor_constants import ExecutorName
from app.domain.executors.context import ExecutorContext
from app.domain.executors.errors import UnknownExecutorError
from app.domain.executors.http_ops import http_request
from app.domain.executors.mongo_ops import (
    mongo_aggregate,
    mongo_delete,
    mongo_find_many,
    mongo_find_one,
    mongo_insert,
    mongo_update,
)

ExecutorFn = Callable[[ExecutorContext], Awaitable[Any]]

EXECUTOR_REGISTRY: dict[str, ExecutorFn] = {
    ExecutorName.MONGO_FIND_ONE: mongo_find_one,
    ExecutorName.MONGO_FIND_MANY: mongo_find_many,
    ExecutorName.MONGO_INSERT: mongo_insert,
    ExecutorName.MONGO_UPDATE: mongo_update,
    ExecutorName.MONGO_DELETE: mongo_delete,
    ExecutorName.MONGO_AGGREGATE: mongo_aggregate,
    ExecutorName.HTTP_REQUEST: http_request,
}


async def run_executor(ctx: ExecutorContext) -> Any:
    fn = EXECUTOR_REGISTRY.get(ctx.executor)
    if fn is None:
        raise UnknownExecutorError(ctx.executor)
    return await fn(ctx)
