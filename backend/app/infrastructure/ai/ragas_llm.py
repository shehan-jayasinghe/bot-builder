from __future__ import annotations

from functools import lru_cache

from langchain_aws import BedrockEmbeddings, ChatBedrockConverse
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from ragas.llms.base import LangchainLLMWrapper

from app.config import settings


def build_ragas_judge_llm(*, temperature: float = 0.0, max_tokens: int = 2048) -> LangchainLLMWrapper:
    model_id = settings.rag_eval_judge_model_id or settings.bedrock_model_id
    client = ChatBedrockConverse(
        model_id=model_id,
        region_name=settings.aws_region,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return LangchainLLMWrapper(client)


@lru_cache(maxsize=1)
def build_ragas_embeddings() -> LangchainEmbeddingsWrapper:
    embeddings = BedrockEmbeddings(
        model_id=settings.bedrock_embed_model_id,
        region_name=settings.aws_region,
    )
    return LangchainEmbeddingsWrapper(embeddings)
