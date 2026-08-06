import logging
import os
from typing import Any

from app.config import settings
from app.domain.pipeline.guardrails.nemo_paths import resolve_nemo_config_path

logger = logging.getLogger(__name__)

# NeMo caches the LLM framework at import time. Force langchain before any
# nemoguardrails import so Bedrock does not hit the default OpenAI-compat path.
_FRAMEWORK = "langchain"
os.environ["NEMOGUARDRAILS_LLM_FRAMEWORK"] = _FRAMEWORK

_rails_instance: Any | None = None


def get_nemo_rails() -> Any:
    global _rails_instance
    if _rails_instance is not None:
        return _rails_instance

    os.environ["NEMOGUARDRAILS_LLM_FRAMEWORK"] = _FRAMEWORK

    from langchain_aws import ChatBedrockConverse
    from nemoguardrails import LLMRails, RailsConfig
    from nemoguardrails.llm.frameworks import set_default_framework

    set_default_framework(_FRAMEWORK)

    config_path = resolve_nemo_config_path(settings.nemo_config_path or None)
    if not config_path.is_dir():
        raise FileNotFoundError(f"NeMo config directory not found: {config_path}")

    # NeMo's amazon_bedrock engine does not work with current langchain-aws
    # (init_chat_model expects bedrock / bedrock_converse). Inject the same
    # ChatBedrockConverse client the rest of the app uses.
    llm = ChatBedrockConverse(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        temperature=0,
        max_tokens=256,
    )

    logger.info(
        "Loading NeMo Guardrails config from %s (llm=%s)",
        config_path,
        settings.bedrock_model_id,
    )
    config = RailsConfig.from_path(str(config_path))
    _rails_instance = LLMRails(config, llm=llm)
    return _rails_instance


def reset_nemo_rails() -> None:
    global _rails_instance
    _rails_instance = None
