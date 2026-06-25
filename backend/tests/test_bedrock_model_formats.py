import pytest

from app.infrastructure.connectors.aws.bedrock_model_formats import (
    BedrockModelFamily,
    build_embed_request,
    build_llm_request,
    detect_model_family,
    parse_embed_response,
    parse_llm_response,
)


@pytest.mark.parametrize(
    ("model_id", "expected"),
    [
        ("amazon.titan-embed-text-v2:0", BedrockModelFamily.TITAN_EMBED),
        ("cohere.embed-v4:0", BedrockModelFamily.COHERE_EMBED),
        ("us.cohere.embed-v4:0", BedrockModelFamily.COHERE_EMBED),
        ("anthropic.claude-haiku-4-5-20251001-v1:0", BedrockModelFamily.ANTHROPIC),
        ("us.anthropic.claude-haiku-4-5-20251001-v1:0", BedrockModelFamily.ANTHROPIC),
        ("amazon.nova-lite-v1:0", BedrockModelFamily.NOVA),
        ("us.amazon.nova-lite-v1:0", BedrockModelFamily.NOVA),
    ],
)
def test_detect_model_family(model_id: str, expected: BedrockModelFamily) -> None:
    assert detect_model_family(model_id) == expected


def test_build_titan_embed_request() -> None:
    body = build_embed_request(
        family=BedrockModelFamily.TITAN_EMBED,
        text="hello",
        dimensions=1024,
    )
    assert body == {"inputText": "hello"}


def test_build_cohere_v4_embed_request() -> None:
    body = build_embed_request(
        family=BedrockModelFamily.COHERE_EMBED,
        text="hello",
        dimensions=1024,
        model_id="us.cohere.embed-v4:0",
    )
    assert body["texts"] == ["hello"]
    assert body["output_dimension"] == 1024


def test_build_anthropic_llm_request() -> None:
    body = build_llm_request(
        family=BedrockModelFamily.ANTHROPIC,
        prompt="hi",
        max_tokens=256,
        temperature=0.0,
    )
    assert body["max_tokens"] == 256
    assert body["messages"][0]["content"] == "hi"


def test_build_nova_llm_request() -> None:
    body = build_llm_request(
        family=BedrockModelFamily.NOVA,
        prompt="hi",
        max_tokens=256,
        temperature=0.0,
    )
    assert body["inferenceConfig"]["maxTokens"] == 256
    assert body["messages"][0]["content"] == [{"text": "hi"}]


def test_parse_anthropic_llm_response() -> None:
    text = parse_llm_response(
        family=BedrockModelFamily.ANTHROPIC,
        payload={"content": [{"text": "ok"}]},
    )
    assert text == "ok"


def test_parse_nova_llm_response() -> None:
    text = parse_llm_response(
        family=BedrockModelFamily.NOVA,
        payload={"output": {"message": {"content": [{"text": "ok"}]}}},
    )
    assert text == "ok"


def test_parse_cohere_embed_response_list_shape() -> None:
    vector = parse_embed_response(
        family=BedrockModelFamily.COHERE_EMBED,
        payload={"embeddings": [[0.1, 0.2]]},
    )
    assert vector == [0.1, 0.2]
