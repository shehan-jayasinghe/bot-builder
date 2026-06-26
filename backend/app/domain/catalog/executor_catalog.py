from typing import Any

from app.domain.constants.executor_constants import ExecutorName


def get_executor_catalog() -> list[dict[str, Any]]:
    return [
        {
            "executor": ExecutorName.MONGO_FIND_ONE,
            "label": "MongoDB — Find One",
            "description": "Retrieve a single document from a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "filter": {"type": "object", "required": True},
                "projection": {"type": "array", "required": False},
            },
        },
        {
            "executor": ExecutorName.MONGO_FIND_MANY,
            "label": "MongoDB — Find Many",
            "description": "Retrieve multiple documents from a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "filter": {"type": "object", "required": True},
                "projection": {"type": "array", "required": False},
                "sort": {"type": "object", "required": False},
                "limit": {"type": "integer", "required": False},
            },
        },
        {
            "executor": ExecutorName.MONGO_INSERT,
            "label": "MongoDB — Insert",
            "description": "Insert one document into a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "document": {"type": "object", "required": True},
            },
        },
        {
            "executor": ExecutorName.MONGO_UPDATE,
            "label": "MongoDB — Update",
            "description": "Update one document in a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "filter": {"type": "object", "required": True},
                "update": {"type": "object", "required": True},
            },
        },
        {
            "executor": ExecutorName.MONGO_DELETE,
            "label": "MongoDB — Delete",
            "description": "Delete one document from a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "filter": {"type": "object", "required": True},
            },
        },
        {
            "executor": ExecutorName.MONGO_AGGREGATE,
            "label": "MongoDB — Aggregate",
            "description": "Run an aggregation pipeline on a collection.",
            "connector_type": "mongo",
            "mvp": True,
            "config_schema": {
                "collection": {"type": "string", "required": True},
                "pipeline": {"type": "array", "required": True},
            },
        },
        {
            "executor": ExecutorName.HTTP_REQUEST,
            "label": "HTTP — Request",
            "description": "Send an HTTP request to a REST API.",
            "connector_type": "http",
            "mvp": True,
            "config_schema": {
                "method": {
                    "type": "enum",
                    "values": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    "required": True,
                },
                "path": {"type": "string", "required": True},
                "headers": {"type": "object", "required": False},
                "query": {"type": "object", "required": False},
                "body": {"type": "object", "required": False},
            },
        },
    ]
