from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[3]
EVAL_DATASETS_ROOT = BACKEND_ROOT / "config" / "eval" / "datasets"
FALLBACK_INDUSTRY = "other"
FALLBACK_AGENT_TYPE = "generic"


def load_builtin_dataset(*, industry: str | None, agent_type: str | None) -> dict[str, Any]:
    industry_key = (industry or FALLBACK_INDUSTRY).strip().lower()
    agent_type_key = (agent_type or FALLBACK_AGENT_TYPE).strip().lower()

    path = EVAL_DATASETS_ROOT / industry_key / f"{agent_type_key}.yml"
    if not path.is_file():
        path = EVAL_DATASETS_ROOT / FALLBACK_INDUSTRY / f"{FALLBACK_AGENT_TYPE}.yml"

    if not path.is_file():
        return _empty_dataset(industry=industry_key, agent_type=agent_type_key)

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    cases = data.get("cases") or []
    return {
        "name": data.get("name") or f"{industry_key} — {agent_type_key} (builtin)",
        "industry": data.get("industry", industry_key),
        "agent_type": data.get("agent_type", agent_type_key),
        "cases": cases,
    }


def builtin_dataset_id(*, industry: str | None, agent_type: str | None) -> str:
    industry_key = (industry or FALLBACK_INDUSTRY).strip().lower()
    agent_type_key = (agent_type or FALLBACK_AGENT_TYPE).strip().lower()
    return f"builtin:{industry_key}:{agent_type_key}"


def _empty_dataset(*, industry: str, agent_type: str) -> dict[str, Any]:
    return {
        "name": f"{industry} — {agent_type} (builtin)",
        "industry": industry,
        "agent_type": agent_type,
        "cases": [],
    }
