"""Short-lived in-process cache for expensive read-only service functions."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_DEFAULT_TTL = 30.0
_store: dict[str, tuple[float, Any]] = {}


def invalidate_cache(prefix: str | None = None) -> None:
    if prefix is None:
        _store.clear()
        return
    for key in list(_store):
        if key.startswith(prefix):
            del _store[key]


def cached_response(ttl_seconds: float = _DEFAULT_TTL, key: str | None = None):
    """Cache the return value of ``fn(conn, ...)`` keyed by function name."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        cache_key = key or fn.__name__

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            now = time.monotonic()
            hit = _store.get(cache_key)
            if hit and now - hit[0] < ttl_seconds:
                return hit[1]
            result = fn(*args, **kwargs)
            _store[cache_key] = (now, result)
            return result

        wrapper.invalidate = lambda: _store.pop(cache_key, None)  # type: ignore[attr-defined]
        return wrapper

    return decorator
