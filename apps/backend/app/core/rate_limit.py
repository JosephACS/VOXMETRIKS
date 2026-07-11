"""Simple in-memory rate limiting for auth and global API endpoints."""

from __future__ import annotations

from collections import defaultdict
from time import time

from fastapi import HTTPException, Request

_buckets: dict[str, list[float]] = defaultdict(list)


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
    client = request.client.host if request.client else "unknown"
    _check_rate_limit(f"global:{client}", max_calls, window_sec)
