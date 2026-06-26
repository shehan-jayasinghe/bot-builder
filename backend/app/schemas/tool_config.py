from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.constants.executor_constants import ExecutorName


class MongoFindOneToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    filter: dict[str, Any]
    projection: list[str] | None = None


class MongoFindManyToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    filter: dict[str, Any]
    projection: list[str] | None = None
    sort: dict[str, int] | None = None
    limit: int | None = Field(default=None, ge=1, le=1000)


class MongoInsertToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    document: dict[str, Any]


class MongoUpdateToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    filter: dict[str, Any]
    update: dict[str, Any]


class MongoDeleteToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    filter: dict[str, Any]


class MongoAggregateToolConfig(BaseModel):
    collection: str = Field(min_length=1)
    pipeline: list[dict[str, Any]] = Field(min_length=1)


class HttpRequestToolConfig(BaseModel):
    method: str = Field(min_length=1)
    path: str = Field(min_length=1)
    headers: dict[str, Any] | None = None
    query: dict[str, Any] | None = None
    body: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_method(self) -> "HttpRequestToolConfig":
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        if self.method.upper() not in allowed:
            raise ValueError(f"method must be one of {sorted(allowed)}")
        return self


_EXECUTOR_CONFIG_MODELS: dict[str, type[BaseModel]] = {
    ExecutorName.MONGO_FIND_ONE: MongoFindOneToolConfig,
    ExecutorName.MONGO_FIND_MANY: MongoFindManyToolConfig,
    ExecutorName.MONGO_INSERT: MongoInsertToolConfig,
    ExecutorName.MONGO_UPDATE: MongoUpdateToolConfig,
    ExecutorName.MONGO_DELETE: MongoDeleteToolConfig,
    ExecutorName.MONGO_AGGREGATE: MongoAggregateToolConfig,
    ExecutorName.HTTP_REQUEST: HttpRequestToolConfig,
}


def parse_tool_config(executor: str, config: dict[str, Any]) -> dict[str, Any]:
    model = _EXECUTOR_CONFIG_MODELS.get(executor)
    if model is None:
        raise ValueError(f"Unsupported executor: {executor}")
    parsed = model.model_validate(config)
    if isinstance(parsed, HttpRequestToolConfig):
        data = parsed.model_dump()
        data["method"] = parsed.method.upper()
        return data
    return parsed.model_dump()
