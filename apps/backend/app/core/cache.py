"""In-memory TTL cache for frequent read-only API queries."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from app.core.config import get_settings

T = TypeVar("T")

_store: dict[str, tuple[float, float, Any]] = {}
_lock = threading.RLock()


def _now() -> float:
    return time.monotonic()


def default_ttl() -> float:
    settings = get_settings()
    return float(settings.cache_ttl_default)


def ttl_for(domain: str) -> float:
    settings = get_settings()
    mapping = {
        "dashboard": settings.cache_ttl_dashboard,
        "analytics": settings.cache_ttl_analytics,
        "top_tracks": settings.cache_ttl_top_tracks,
        "recommendations": settings.cache_ttl_recommendations,
        "smart_home": settings.cache_ttl_smart_home,
        "audio": settings.cache_ttl_audio,
    }
    return float(mapping.get(domain, settings.cache_ttl_default))


def make_cache_key(prefix: str, *parts: Any) -> str:
    raw = json.dumps([prefix, *parts], default=str, sort_keys=True)
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{prefix}:{digest}"


def cache_get(key: str) -> Any | None:
    settings = get_settings()
    if not settings.cache_enabled:
        return None
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        expires_at, _, value = entry
        if _now() > expires_at:
            del _store[key]
            return None
        return value


def cache_set(key: str, value: Any, ttl_seconds: float | None = None) -> None:
    settings = get_settings()
    if not settings.cache_enabled:
        return
    ttl = ttl_seconds if ttl_seconds is not None else default_ttl()
    with _lock:
        _store[key] = (_now() + ttl, ttl, value)


def cache_invalidate(prefix: str | None = None) -> int:
    with _lock:
        if prefix is None:
            count = len(_store)
            _store.clear()
            return count
        keys = [k for k in _store if k.startswith(prefix)]
        for key in keys:
            del _store[key]
        return len(keys)


def cache_stats() -> dict:
    """Observability snapshot for platform status."""
    settings = get_settings()
    with _lock:
        now = _now()
        active = sum(1 for exp, _, _ in _store.values() if exp > now)
        prefixes: dict[str, int] = {}
        for key in _store:
            p = key.split(":", 1)[0]
            prefixes[p] = prefixes.get(p, 0) + 1
    return {
        "enabled": settings.cache_enabled,
        "entries": active,
        "prefixes": prefixes,
    }


def cached(ttl_seconds: float | None = None, key_prefix: str | None = None):
    """Decorator caching function results by prefix + arguments."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        prefix = key_prefix or fn.__qualname__

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache_key = make_cache_key(prefix, args[1:], kwargs)
            hit = cache_get(cache_key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            cache_set(cache_key, result, ttl_seconds)
            return result

        wrapper.cache_invalidate = lambda: cache_invalidate(prefix)  # type: ignore[attr-defined]
        return wrapper

    return decorator
