from __future__ import annotations

import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from quantvibe.core.config import load_config


class ConfigTest(unittest.TestCase):
    def test_load_config_merges_local_and_resolves_cache_dir_from_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            default_path = temp_path / "default.yaml"
            local_path = temp_path / "local.yaml"
            runtime_root = temp_path / "runtime"
            default_path.write_text(
                textwrap.dedent(
                    """
                    data:
                      cache_dir: ./cache
                    backtest:
                      top_n: 2
                    """
                ).strip()
            )
            local_path.write_text(
                textwrap.dedent(
                    """
                    backtest:
                      top_n: 1
                    """
                ).strip()
            )

            with patch.dict(os.environ, {"QUANTVIBE_RUNTIME_DIR": str(runtime_root)}, clear=False):
                config = load_config(default_path=default_path, local_path=local_path)

            self.assertEqual(config["backtest"]["top_n"], 1)
            self.assertEqual(config["data"]["cache_dir"], str(runtime_root / "cache"))

    def test_load_config_skips_missing_local_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            default_path = temp_path / "default.yaml"
            runtime_root = temp_path / "runtime"
            default_path.write_text(
                textwrap.dedent(
                    """
                    data:
                      cache_dir: ./cache
                    providers:
                      crypto:
                        exchange_id: binance
                    """
                ).strip()
            )

            with patch.dict(os.environ, {"QUANTVIBE_RUNTIME_DIR": str(runtime_root)}, clear=False):
                config = load_config(default_path=default_path, local_path=temp_path / "missing.yaml")

            self.assertEqual(config["providers"]["crypto"]["exchange_id"], "binance")
            self.assertEqual(config["data"]["cache_dir"], str(runtime_root / "cache"))

