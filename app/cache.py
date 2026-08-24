"""Cache de API no MongoDB (collection api_cache). Sem Redis."""

from __future__ import annotations

from typing import Any, Optional


def cache_status() -> dict[str, Any]:
    return {
        "backend": "mongo",
        "collection": "api_cache",
        "enabled": True,
        "connected": True,
        "kinds": ["hunter_scan (~30min)", "orders_history (~5min)", "candles (~30min)"],
    }


# Alias antigo (status UI)
def redis_status() -> dict[str, Any]:
    return cache_status()


def get_api_cache(key: str, ttl_s: float) -> Optional[dict[str, Any]]:
    from . import db as mongo_db

    return mongo_db._mongo_get_api_cache(key, ttl_s)


def set_api_cache(
    key: str,
    payload: dict[str, Any],
    *,
    kind: str = "",
    ttl_s: float = 600.0,
) -> None:
    del ttl_s  # TTL aplicado na leitura; Mongo guarda ts
    from . import db as mongo_db

    mongo_db._mongo_set_api_cache(key, payload, kind=kind)


def clear_api_cache(*, kind: Optional[str] = None) -> None:
    from . import db as mongo_db

    mongo_db._mongo_clear_api_cache(kind=kind)
