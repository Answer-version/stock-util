from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(
    default_path: str | Path = "config/default.yaml",
    local_path: str | Path | None = "config/local.yaml",
) -> dict[str, Any]:
    default_data = yaml.safe_load(Path(default_path).read_text()) or {}
    if local_path is None or not Path(local_path).exists():
        return default_data
    local_data = yaml.safe_load(Path(local_path).read_text()) or {}
    return _deep_merge(default_data, local_data)
