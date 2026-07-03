from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from quantvibe.core.paths import ensure_runtime_layout, local_config_path, resource_path, runtime_path


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(
    default_path: str | Path | None = None,
    local_path: str | Path | None = None,
) -> dict[str, Any]:
    ensure_runtime_layout()

    resolved_default_path = Path(
        os.getenv("QUANTVIBE_DEFAULT_CONFIG") or default_path or resource_path("config", "default.yaml")
    )
    default_data = yaml.safe_load(resolved_default_path.read_text()) or {}

    resolved_local_path = Path(local_path) if local_path is not None else local_config_path()
    merged = default_data
    if resolved_local_path.exists():
        local_data = yaml.safe_load(resolved_local_path.read_text()) or {}
        merged = _deep_merge(default_data, local_data)
    return _resolve_runtime_paths(merged)


def _resolve_runtime_paths(config: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(config)
    data_config = dict(resolved.get("data", {}))
    cache_dir = data_config.get("cache_dir")
    if cache_dir:
        data_config["cache_dir"] = str(runtime_path(cache_dir))
    resolved["data"] = data_config
    return resolved
