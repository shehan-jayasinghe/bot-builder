from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.domain.pipeline.guardrails.nemo_gate_models import NeMoGateContext, NeMoGateIntent, ScriptedMatch
from app.domain.pipeline.guardrails.nemo_paths import resolve_nemo_config_path

logger = logging.getLogger(__name__)

_INTENT_BY_ID: dict[str, NeMoGateIntent] = {
    "greeting": NeMoGateIntent.GREETING,
    "help": NeMoGateIntent.HELP,
    "bye": NeMoGateIntent.BYE,
}


@dataclass(frozen=True)
class ScriptedIntentDef:
    id: str
    phrases: tuple[str, ...]
    reply: str


def _normalize_user_text(text: str) -> str:
    cleaned = text.strip().lower()
    return re.sub(r"[!?.]+$", "", cleaned).strip()


def _format_reply(template: str, *, context: NeMoGateContext) -> str:
    values = {
        "agent_name": context.agent_name,
        "industry": context.industry or "your industry",
    }
    try:
        return template.format(**values)
    except KeyError:
        logger.warning("Scripted reply template has unknown placeholders; using raw template")
        return template


@lru_cache(maxsize=4)
def load_scripted_intents(config_dir: str) -> tuple[ScriptedIntentDef, ...]:
    path = Path(config_dir) / "scripted_intents.yml"
    if not path.is_file():
        raise FileNotFoundError(f"Scripted intents config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    intents: list[ScriptedIntentDef] = []
    for item in raw.get("intents") or []:
        intent_id = str(item["id"])
        phrases = tuple(str(p).strip().lower() for p in item.get("phrases") or [])
        reply = str(item["reply"])
        intents.append(ScriptedIntentDef(id=intent_id, phrases=phrases, reply=reply))
    return tuple(intents)


def get_scripted_intents(*, config_path: str | None = None) -> tuple[ScriptedIntentDef, ...]:
    return load_scripted_intents(str(resolve_nemo_config_path(config_path or None)))


def match_scripted_intent(
    message: str,
    *,
    context: NeMoGateContext,
    config_path: str | None = None,
) -> ScriptedMatch | None:
    normalized = _normalize_user_text(message)
    if not normalized:
        return None

    for intent_def in get_scripted_intents(config_path=config_path):
        gate_intent = _INTENT_BY_ID.get(intent_def.id)
        if gate_intent is None:
            continue
        for phrase in intent_def.phrases:
            if normalized == phrase:
                return ScriptedMatch(
                    intent=gate_intent,
                    matched_phrase=phrase,
                    reply=_format_reply(intent_def.reply, context=context),
                )
    return None


def reset_scripted_intents_cache() -> None:
    load_scripted_intents.cache_clear()
