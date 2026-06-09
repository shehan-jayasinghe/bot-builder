from pydantic import BaseModel, Field


class AssistantCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    webhook_id: str = Field(..., min_length=1)


class AssistantResponse(BaseModel):
    id: str
    name: str
    webhook_id: str
    system_prompt: str

    # TODO: expose flows, slots, knowledge_base_ids in API responses
