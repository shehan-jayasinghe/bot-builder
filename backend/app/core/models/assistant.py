from pydantic import BaseModel, Field


class DialogueAssistant(BaseModel):
    id: str
    name: str
    webhook_id: str
    system_prompt: str

    # TODO: flows — list of conversation flow definitions
    # TODO: slots — domain slots for slot filling
    # TODO: llm_config — model_id, temperature, max_tokens from assistant settings
    # TODO: knowledge_base_ids — refs for RAG retrieval

    temperature: float = Field(default=0.7)
    max_output_tokens: int = Field(default=1024)
