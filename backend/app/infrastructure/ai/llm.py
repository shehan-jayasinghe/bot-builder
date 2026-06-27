from typing import Any

from app.config import settings


class BedrockLLM:
    def __init__(
        self,
        *,
        model_id: str | None = None,
        region: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> None:
        self._model_id = model_id or settings.bedrock_model_id
        self._region = region or settings.aws_region
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            from langchain_aws import ChatBedrockConverse

            self._client = ChatBedrockConverse(
                model_id=self._model_id,
                region_name=self._region,
                temperature=self._temperature,
                max_tokens=self._max_output_tokens,
            )

        return self._client

    def get_client(self):
        return self._get_client()

    async def chat_from_history(
        self,
        *,
        system_prompt: str,
        history: list[dict[str, Any]],
    ) -> str:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages: list[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=system_prompt),
        ]
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=str(content)))
            elif role == "assistant":
                messages.append(AIMessage(content=str(content)))

        response = await self._get_client().ainvoke(messages)
        return str(response.content)

    async def chat(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[dict[str, Any]],
    ) -> str:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages: list[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=system_prompt),
        ]

        # TODO: convert tracker history to LangChain messages with proper typing
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=str(content)))
            elif role == "assistant":
                messages.append(AIMessage(content=str(content)))

        messages.append(HumanMessage(content=user_message))

        # TODO: add streaming support for real-time chat UIs
        # TODO: add Langfuse / CloudWatch tracing and token cost logging
        response = await self._get_client().ainvoke(messages)
        return str(response.content)
