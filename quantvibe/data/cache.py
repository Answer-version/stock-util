from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


class DataCache:
    def __init__(self, cache_dir: str = "./cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: dict[str, Any]) -> tuple[Path, Path]:
        payload = json.dumps(key, sort_keys=True, ensure_ascii=True).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return self.cache_dir / f"{digest}.parquet", self.cache_dir / f"{digest}.json"

    def get(self, key: dict[str, Any]) -> pd.DataFrame | None:
        data_path, meta_path = self._paths(key)
        if not data_path.exists() or not meta_path.exists():
            return None
        metadata = json.loads(meta_path.read_text())
        expires_at = pd.Timestamp(metadata["expires_at"])
        if expires_at < pd.Timestamp.now(tz="UTC"):
            self.delete(key)
            return None
        return pd.read_parquet(data_path)

    def set(self, key: dict[str, Any], df: pd.DataFrame, ttl_seconds: int = 86400) -> None:
        data_path, meta_path = self._paths(key)
        df.to_parquet(data_path)
        metadata = {
            "key": key,
            "expires_at": (pd.Timestamp.now(tz="UTC") + pd.Timedelta(seconds=ttl_seconds)).isoformat(),
        }
        meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))

    def delete(self, key: dict[str, Any]) -> None:
        data_path, meta_path = self._paths(key)
        if data_path.exists():
            data_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def invalidate_expired(self) -> int:
        removed = 0
        for meta_path in self.cache_dir.glob("*.json"):
            metadata = json.loads(meta_path.read_text())
            expires_at = pd.Timestamp(metadata["expires_at"])
            if expires_at < pd.Timestamp.now(tz="UTC"):
                data_path = meta_path.with_suffix(".parquet")
                if data_path.exists():
                    data_path.unlink()
                meta_path.unlink()
                removed += 1
        return removed
