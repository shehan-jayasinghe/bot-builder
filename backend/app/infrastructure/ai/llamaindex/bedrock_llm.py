from typing import Any

from llama_index.core.base.llms.types import CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.llms.custom import CustomLLM

from app.config import settings
from app.infrastructure.connectors.aws.bedrock_connector import BedrockConnector


class BedrockLlamaLLM(CustomLLM):
    """LlamaIndex LLM adapter over AWS Bedrock for graph extraction."""

    def __init__(
        self,
        *,
        connector: BedrockConnector | None = None,
        model_name: str | None = None,
        max_tokens: int = 1024,
    ) -> None:
        super().__init__()
        self._connector = connector or BedrockConnector(
            region=settings.aws_region,
            embed_model_id=settings.bedrock_embed_model_id,
            llm_model_id=settings.bedrock_model_id,
            embed_dimensions=settings.bedrock_embed_dimensions,
        )
        self._model_name = model_name or settings.bedrock_model_id
        self._max_tokens = max_tokens

    @classmethod
    def class_name(cls) -> str:
        return "BedrockLlamaLLM"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            model_name=self._model_name,
            context_window=200_000,
            num_output=self._max_tokens,
            is_chat_model=False,
        )

    @llm_completion_callback()
    def complete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ) -> CompletionResponse:
        max_tokens = int(kwargs.get("max_tokens", self._max_tokens))
        temperature = float(kwargs.get("temperature", 0.0))
        text = self._connector.invoke_llm(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ):
        yield self.complete(prompt, formatted=formatted, **kwargs)
