from llama_index.core.base.embeddings.base import BaseEmbedding

from app.config import settings
from app.infrastructure.connectors.aws.bedrock_connector import BedrockConnector


class BedrockLlamaEmbedding(BaseEmbedding):
    """LlamaIndex embedding adapter over AWS Bedrock Titan."""

    def __init__(
        self,
        *,
        connector: BedrockConnector | None = None,
        model_name: str | None = None,
        embed_batch_size: int = 16,
    ) -> None:
        connector = connector or BedrockConnector(
            region=settings.aws_region,
            embed_model_id=settings.bedrock_embed_model_id,
            llm_model_id=settings.bedrock_model_id,
            embed_dimensions=settings.bedrock_embed_dimensions,
        )
        super().__init__(
            model_name=model_name or settings.bedrock_embed_model_id,
            embed_batch_size=embed_batch_size,
        )
        self._connector = connector

    @classmethod
    def class_name(cls) -> str:
        return "BedrockLlamaEmbedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._connector.embed_text(text=query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._connector.embed_text(text=text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._connector.embed_texts(texts=texts)
