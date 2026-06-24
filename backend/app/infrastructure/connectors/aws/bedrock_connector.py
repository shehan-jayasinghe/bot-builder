import json
import logging
import os

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockConnector:
    """AWS Bedrock connector for embeddings and LLM invoke."""

    def __init__(
        self,
        *,
        region: str | None = None,
        embed_model_id: str | None = None,
        llm_model_id: str | None = None,
    ) -> None:
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._embed_model_id = embed_model_id or os.getenv(
            "BEDROCK_EMBED_MODEL",
            "amazon.titan-embed-text-v2:0",
        )
        self._llm_model_id = llm_model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
        )
        self._client: BaseClient | None = None

    @property
    def embed_model_id(self) -> str:
        return self._embed_model_id

    @property
    def llm_model_id(self) -> str:
        return self._llm_model_id

    def _get_client(self) -> BaseClient:
        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    def embed_text(self, *, text: str) -> list[float]:
        """Return a dense embedding vector for a single text input."""
        body = json.dumps({"inputText": text})
        try:
            response = self._get_client().invoke_model(
                modelId=self._embed_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
            embedding = payload.get("embedding")
            if not embedding:
                raise ValueError("Bedrock embed response missing 'embedding'")
            return embedding
        except ClientError:
            logger.exception("Bedrock embed failed for model %s", self._embed_model_id)
            raise

    def embed_texts(self, *, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text=text) for text in texts]

    def invoke_llm(
        self,
        *,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """Invoke the configured LLM and return the text response."""
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        try:
            response = self._get_client().invoke_model(
                modelId=self._llm_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
            content = payload.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return str(payload)
        except ClientError:
            logger.exception("Bedrock LLM invoke failed for model %s", self._llm_model_id)
            raise

    def ping(self) -> bool:
        try:
            bedrock = boto3.client("bedrock", region_name=self._region)
            bedrock.list_foundation_models(byOutputModality="EMBEDDING", maxResults=1)
            return True
        except ClientError:
            logger.warning("Bedrock not reachable in region %s", self._region)
            return False
