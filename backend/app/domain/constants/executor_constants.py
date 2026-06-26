from enum import StrEnum


class ExecutorName(StrEnum):
    MONGO_FIND_ONE = "mongo_find_one"
    MONGO_FIND_MANY = "mongo_find_many"
    MONGO_INSERT = "mongo_insert"
    MONGO_UPDATE = "mongo_update"
    MONGO_DELETE = "mongo_delete"
    MONGO_AGGREGATE = "mongo_aggregate"
    HTTP_REQUEST = "http_request"


MVP_EXECUTORS: frozenset[str] = frozenset(ExecutorName)

EXECUTOR_CONNECTOR_TYPES: dict[str, str] = {
    ExecutorName.MONGO_FIND_ONE: "mongo",
    ExecutorName.MONGO_FIND_MANY: "mongo",
    ExecutorName.MONGO_INSERT: "mongo",
    ExecutorName.MONGO_UPDATE: "mongo",
    ExecutorName.MONGO_DELETE: "mongo",
    ExecutorName.MONGO_AGGREGATE: "mongo",
    ExecutorName.HTTP_REQUEST: "http",
}
