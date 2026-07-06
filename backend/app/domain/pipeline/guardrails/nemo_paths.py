from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[4]


def resolve_nemo_config_path(override: str | None = None) -> Path:
    if override:
        return Path(override)
    return _BACKEND_ROOT / "config" / "nemo" / "profiles" / "default"
