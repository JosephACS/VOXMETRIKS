"""Simple in-memory rate limiting for auth and global API endpoints."""

from __future__ import annotations

from collections import defaultdict
from time import time

from fastapi import HTTPException, Request

_buckets: dict[str, list[float]] = defaultdict(list)

# Home/smart grids fire dozens of cover + audio lookups at once; these are
# cached GETs and must not compete with the global API budget.
_RATE_LIMIT_EXEMPT_SUFFIXES = (
    "/cover",
    "/audio-source",
)
_RATE_LIMIT_EXEMPT_PATHS = {
    "/health",
    "/api/v1/health",
    "/api/health",
}


def is_rate_limit_exempt(path: str) -> bool:
    if path in _RATE_LIMIT_EXEMPT_PATHS:
        return True
    return any(path.endswith(suffix) for suffix in _RATE_LIMIT_EXEMPT_SUFFIXES)


def clear_rate_limit_buckets() -> None:
    """Reset in-memory counters (useful after local 429 storms)."""
    _buckets.clear()


def _check_rate_limit(key: str, max_calls: int, window_sec: int) -> None:
    if max_calls <= 0:
        return
    now = time()
    bucket = _buckets[key]
    bucket[:] = [t for t in bucket if now - t < window_sec]
    if len(bucket) >= max_calls:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    bucket.append(now)


def check_auth_rate_limit(request: Request, max_calls: int, window_sec: int) -> None:
    client = request.client.host if request.client else "unknown"
    _check_rate_limit(f"auth:{client}", max_calls, window_sec)


def check_global_rate_limit(request: Request, max_calls: int, window_sec: int) -> None:
    if is_rate_limit_exempt(request.url.path):
        return
    client = request.client.host if request.client else "unknown"
    _check_rate_limit(f"global:{client}", max_calls, window_sec)
