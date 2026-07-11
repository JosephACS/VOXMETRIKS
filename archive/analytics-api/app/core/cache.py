from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("voxmetrik.analytics.cache")

T = TypeVar("T")

_lock = threading.Lock()
_store: OrderedDict[str, tuple[float, Any]] = OrderedDict()


def _cache_key(prefix: str, *parts: Any) -> str:
    raw = json.dumps([prefix, *parts], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _evict_expired(now: float, ttl: int) -> None:
    expired = [k for k, (ts, _) in _store.items() if now - ts > ttl]
    for key in expired:
        _store.pop(key, None)


def _enforce_max(max_entries: int) -> None:
    while len(_store) > max_entries:
        _store.popitem(last=False)


def cache_get(key: str) -> Any | None:
    settings = get_settings()
    if not settings.cache_enabled:
        return None
    now = time.monotonic()
    with _lock:
        _evict_expired(now, settings.cache_ttl_seconds)
        item = _store.get(key)
        if item is None:
            return None
        ts, value = item
        if now - ts > settings.cache_ttl_seconds:
            _store.pop(key, None)
            return None
        _store.move_to_end(key)
        return value


def cache_set(key: str, value: Any) -> None:
    settings = get_settings()
    if not settings.cache_enabled:
        return
    now = time.monotonic()
    with _lock:
        _evict_expired(now, settings.cache_ttl_seconds)
        _store[key] = (now, value)
        _store.move_to_end(key)
        _enforce_max(settings.cache_max_entries)


def cached_call(prefix: str, builder: Callable[[], T], *key_parts: Any) -> T:
    key = _cache_key(prefix, *key_parts)
    hit = cache_get(key)
    if hit is not None:
        logger.debug("cache_hit prefix=%s", prefix)
        return hit
    value = builder()
    cache_set(key, value)
    logger.debug("cache_miss prefix=%s", prefix)
    return value


def cache_clear() -> None:
    with _lock:
        _store.clear()
