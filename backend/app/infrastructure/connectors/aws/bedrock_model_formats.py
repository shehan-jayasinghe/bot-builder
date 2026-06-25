from enum import StrEnum
from typing import Any


class BedrockModelFamily(StrEnum):
    TITAN_EMBED = "titan_embed"
    COHERE_EMBED = "cohere_embed"
    ANTHROPIC = "anthropic"
    NOVA = "nova"
    UNKNOWN = "unknown"


def detect_model_family(model_id: str) -> BedrockModelFamily:
    """Infer request/response format from a Bedrock model or inference profile ID."""
    model_key = model_id.lower()

    if "titan-embed" in model_key or "titan_embed" in model_key:
        return BedrockModelFamily.TITAN_EMBED
    if "cohere.embed" in model_key:
        return BedrockModelFamily.COHERE_EMBED
    if "anthropic" in model_key or "claude" in model_key:
        return BedrockModelFamily.ANTHROPIC
    if "nova" in model_key:
        return BedrockModelFamily.NOVA

    return BedrockModelFamily.UNKNOWN


def build_embed_request(
    *,
    family: BedrockModelFamily,
    text: str,
    dimensions: int,
    model_id: str = "",
) -> dict[str, Any]:
    if family == BedrockModelFamily.TITAN_EMBED:
        return {"inputText": text}

    if family == BedrockModelFamily.COHERE_EMBED:
        body: dict[str, Any] = {
            "texts": [text],
            "input_type": "search_document",
            "embedding_types": ["float"],
        }
        if "embed-v4" in model_id.lower():
            body["output_dimension"] = dimensions
        return body

    raise ValueError(f"Unsupported embed model family: {family}")


def parse_embed_response(*, family: BedrockModelFamily, payload: dict[str, Any]) -> list[float]:
    if family == BedrockModelFamily.TITAN_EMBED:
        embedding = payload.get("embedding")
        if not embedding:
            raise ValueError("Bedrock Titan embed response missing 'embedding'")
        return embedding

    if family == BedrockModelFamily.COHERE_EMBED:
        embeddings = payload.get("embeddings")
        if not embeddings or not isinstance(embeddings, list):
            raise ValueError("Bedrock Cohere embed response missing 'embeddings'")
        first = embeddings[0]
        if isinstance(first, dict):
            floats = first.get("float")
            if floats:
                return floats
        if isinstance(first, list):
            return first
        raise ValueError("Bedrock Cohere embed response has unexpected embedding shape")

    raise ValueError(f"Unsupported embed model family: {family}")


def build_llm_request(
    *,
    family: BedrockModelFamily,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    if family == BedrockModelFamily.ANTHROPIC:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

    if family == BedrockModelFamily.NOVA:
        return {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }

    raise ValueError(f"Unsupported LLM model family: {family}")


def parse_llm_response(*, family: BedrockModelFamily, payload: dict[str, Any]) -> str:
    if family == BedrockModelFamily.ANTHROPIC:
        content = payload.get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text", "")
            if text:
                return text
        raise ValueError("Bedrock Anthropic response missing text content")

    if family == BedrockModelFamily.NOVA:
        message = payload.get("output", {}).get("message", {})
        blocks = message.get("content", [])
        if blocks and isinstance(blocks, list):
            text = blocks[0].get("text", "")
            if text:
                return text
        raise ValueError("Bedrock Nova response missing text content")

    raise ValueError(f"Unsupported LLM model family: {family}")
