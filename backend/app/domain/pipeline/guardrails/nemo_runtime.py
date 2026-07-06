import logging
import os
from typing import Any

from app.config import settings
from app.domain.pipeline.guardrails.nemo_paths import resolve_nemo_config_path

logger = logging.getLogger(__name__)

_rails_instance: Any | None = None


def get_nemo_rails() -> Any:
    global _rails_instance
    if _rails_instance is not None:
        return _rails_instance

    os.environ.setdefault("NEMOGUARDRAILS_LLM_FRAMEWORK", "langchain")

    from nemoguardrails import LLMRails, RailsConfig

    config_path = resolve_nemo_config_path(settings.nemo_config_path or None)
    if not config_path.is_dir():
        raise FileNotFoundError(f"NeMo config directory not found: {config_path}")

    logger.info("Loading NeMo Guardrails config from %s", config_path)
    config = RailsConfig.from_path(str(config_path))
    _rails_instance = LLMRails(config)
    return _rails_instance


def reset_nemo_rails() -> None:
    global _rails_instance
    _rails_instance = None
