from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, model_validator


class SourceType(StrEnum):
    FILE = "file"
    WEBSITE = "website"


class StorageType(StrEnum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    GRAPH = "graph"


class CreateKnowledgebaseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    source_type: SourceType
    storage_type: StorageType
    website_url: HttpUrl | None = None
    crawl_depth: int | None = Field(default=None, ge=1, le=5)
    agent_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{24}$")

    @model_validator(mode="after")
    def validate_source_fields(self) -> "CreateKnowledgebaseRequest":
        if self.source_type == SourceType.FILE:
            if self.website_url is not None:
                raise ValueError("website_url must be omitted when source_type is file")
            if self.crawl_depth is not None:
                raise ValueError("crawl_depth must be omitted when source_type is file")
        elif self.source_type == SourceType.WEBSITE:
            if self.website_url is None:
                raise ValueError("website_url is required when source_type is website")
            if self.crawl_depth is None:
                raise ValueError("crawl_depth is required when source_type is website")
        return self


class CreateKnowledgebaseResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    organization_id: str
    source_type: SourceType
    storage_type: StorageType
    website_url: str | None = None
    crawl_depth: int | None = None
    agent_id: str | None = None
    status: str
    job_id: str
    job_status: str
    created_at: datetime


class KnowledgebaseStatus(StrEnum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class KnowledgebaseListItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    source_type: SourceType
    storage_type: StorageType
    website_url: str | None = None
    crawl_depth: int | None = None
    agent_id: str | None = None
    status: str
    organization_id: str
    created_at: datetime


class ListKnowledgebasesResponse(BaseModel):
    items: list[KnowledgebaseListItem]
    total: int


class UpdateKnowledgebaseRequest(BaseModel):
    agent_id: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{24}$")

    @model_validator(mode="after")
    def validate_not_empty(self) -> "UpdateKnowledgebaseRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class UpdateKnowledgebaseResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    source_type: SourceType
    storage_type: StorageType
    website_url: str | None = None
    crawl_depth: int | None = None
    agent_id: str | None = None
    status: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class IngestKnowledgebasePayload(BaseModel):
    knowledgebase_id: str
    job_id: str
    organization_id: str
    source_type: SourceType
    storage_type: StorageType
    website_url: str | None = None
    crawl_depth: int | None = None
    agent_id: str | None = None
    s3_key: str | None = None

    def to_task_dict(self) -> dict[str, str | int | None]:
        return {
            "knowledgebase_id": self.knowledgebase_id,
            "job_id": self.job_id,
            "organization_id": self.organization_id,
            "source_type": self.source_type.value,
            "storage_type": self.storage_type.value,
            "website_url": self.website_url,
            "crawl_depth": self.crawl_depth,
            "agent_id": self.agent_id,
            "s3_key": self.s3_key,
        }
