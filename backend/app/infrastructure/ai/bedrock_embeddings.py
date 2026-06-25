from app.config import settings
from app.infrastructure.connectors.aws.bedrock_connector import BedrockConnector


class BedrockEmbeddings:
    """Titan embeddings via AWS Bedrock for vector indexing."""

    def __init__(self, connector: BedrockConnector | None = None) -> None:
        self._connector = connector or BedrockConnector(
            region=settings.aws_region,
            embed_model_id=settings.bedrock_embed_model_id,
            llm_model_id=settings.bedrock_model_id,
            embed_dimensions=settings.bedrock_embed_dimensions,
        )

    @property
    def dimensions(self) -> int:
        return settings.bedrock_embed_dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._connector.embed_texts(texts=texts)

    def embed_query(self, text: str) -> list[float]:
        return self._connector.embed_text(text=text)
