from app.config import settings


class BedrockEmbeddings:
    """
    Embedding model wrapper for RAG.

    TODO:
      - wire langchain-aws BedrockEmbeddings (amazon.titan-embed-text-v2)
      - use for knowledge base indexing and retrieval
      - align vector dimensions with Qdrant collection config
    """

    def __init__(self, region: str | None = None) -> None:
        self._region = region or settings.aws_region

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        _ = texts
        raise NotImplementedError("Bedrock embeddings are not implemented yet.")

    async def embed_query(self, text: str) -> list[float]:
        _ = text
        raise NotImplementedError("Bedrock embeddings are not implemented yet.")
