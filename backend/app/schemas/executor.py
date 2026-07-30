from typing import Any

from pydantic import BaseModel

from app.domain.constants.executor_constants import ExecutorName


class ExecutorCatalogItem(BaseModel):
    executor: ExecutorName
    label: str
    description: str
    connector_type: str
    mvp: bool
    config_schema: dict[str, Any]


class ListExecutorsResponse(BaseModel):
    items: list[ExecutorCatalogItem]
