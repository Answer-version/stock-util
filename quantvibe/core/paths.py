from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from platformdirs import user_data_dir


APP_NAME = "QuantVibe"
APP_AUTHOR = "Answer-version"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return repo_root()


def resource_path(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)


def runtime_root() -> Path:
    override = os.getenv("QUANTVIBE_RUNTIME_DIR")
    if override:
        root = Path(override).expanduser()
    elif getattr(sys, "frozen", False):
        root = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    else:
        root = repo_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def runtime_path(path_str: str | Path) -> Path:
    candidate = Path(path_str).expanduser()
    if candidate.is_absolute():
        return candidate
    return runtime_root() / candidate


def config_dir() -> Path:
    path = runtime_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_config_path() -> Path:
    override = os.getenv("QUANTVIBE_LOCAL_CONFIG")
    if override:
        return runtime_path(override)
    dev_path = repo_root() / "config" / "local.yaml"
    if dev_path.exists() and not getattr(sys, "frozen", False):
        return dev_path
    return config_dir() / "local.yaml"


def ensure_runtime_layout() -> None:
    root = runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "cache").mkdir(parents=True, exist_ok=True)

    runtime_config_dir = config_dir()
    bundled_example = resource_path("config", "local.yaml.example")
    runtime_example = runtime_config_dir / "local.yaml.example"
    if bundled_example.exists() and bundled_example.resolve() != runtime_example.resolve() and not runtime_example.exists():
        shutil.copyfile(bundled_example, runtime_example)

