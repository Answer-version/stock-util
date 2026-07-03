from __future__ import annotations

from typing import Any

from quantvibe.data.base import BaseProvider
from quantvibe.data.providers.crypto_ccxt import CryptoCCXTProvider

PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {
    "crypto_ccxt": CryptoCCXTProvider,
}


def get_provider(name: str, **kwargs: Any) -> BaseProvider:
    try:
        provider_cls = PROVIDER_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown provider: {name}") from exc
    return provider_cls(**kwargs)
