# -*- coding: utf-8 -*-
"""YouTube Data API search guard: cache, concurrency dedupe, soft quotas."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_INFLIGHT: Dict[str, threading.Event] = {}
_INFLIGHT_RESULT: Dict[str, List[Dict[str, Any]]] = {}
_USER_HITS: Dict[int, List[float]] = {}
_GLOBAL_HITS: List[float] = []

# Soft limits (in-process; reset on restart)
CACHE_TTL_SEC = 600.0
USER_LIMIT_PER_HOUR = 40
GLOBAL_LIMIT_PER_HOUR = 300
MAX_CACHE_ENTRIES = 256


def _prune(now: float) -> None:
    expired = [k for k, (ts, _) in _CACHE.items() if now - ts > CACHE_TTL_SEC]
    for k in expired:
        _CACHE.pop(k, None)
    if len(_CACHE) > MAX_CACHE_ENTRIES:
        oldest = sorted(_CACHE.items(), key=lambda x: x[1][0])[
            : len(_CACHE) - MAX_CACHE_ENTRIES
        ]
        for k, _ in oldest:
            _CACHE.pop(k, None)
    cutoff = now - 3600.0
    global _GLOBAL_HITS
    _GLOBAL_HITS = [t for t in _GLOBAL_HITS if t >= cutoff]
    for uid in list(_USER_HITS.keys()):
        _USER_HITS[uid] = [t for t in _USER_HITS[uid] if t >= cutoff]
        if not _USER_HITS[uid]:
            _USER_HITS.pop(uid, None)


def check_quota(user_id: Optional[int] = None) -> Optional[str]:
    """Return error phase code if quota exhausted, else None."""
    now = time.time()
    with _LOCK:
        _prune(now)
        if len(_GLOBAL_HITS) >= GLOBAL_LIMIT_PER_HOUR:
            return "quota_exhausted"
        if user_id is not None:
            hits = _USER_HITS.get(int(user_id), [])
            if len(hits) >= USER_LIMIT_PER_HOUR:
                return "quota_exhausted"
    return None


def get_cached(normalized_query: str) -> Optional[List[Dict[str, Any]]]:
    now = time.time()
    with _LOCK:
        _prune(now)
        hit = _CACHE.get(normalized_query)
        if not hit:
            return None
        ts, payload = hit
        if now - ts > CACHE_TTL_SEC:
            _CACHE.pop(normalized_query, None)
            return None
        return list(payload)


def put_cache(normalized_query: str, results: List[Dict[str, Any]]) -> None:
    now = time.time()
    with _LOCK:
        _CACHE[normalized_query] = (now, list(results))


def record_usage(user_id: Optional[int] = None) -> None:
    now = time.time()
    with _LOCK:
        _GLOBAL_HITS.append(now)
        if user_id is not None:
            _USER_HITS.setdefault(int(user_id), []).append(now)


def search_with_guard(
    *,
    normalized_query: str,
    user_id: Optional[int],
    fetch: Callable[[], List[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Returns (results, status) where status is:
    ok | cache_hit | quota_exhausted | error
    """
    cached = get_cached(normalized_query)
    if cached is not None:
        return cached, "cache_hit"

    quota = check_quota(user_id)
    if quota:
        return [], quota

    # Concurrent dedupe for identical queries
    wait_event: Optional[threading.Event] = None
    leader = False
    with _LOCK:
        if normalized_query in _INFLIGHT:
            wait_event = _INFLIGHT[normalized_query]
        else:
            wait_event = threading.Event()
            _INFLIGHT[normalized_query] = wait_event
            leader = True

    if not leader and wait_event is not None:
        wait_event.wait(timeout=25.0)
        with _LOCK:
            result = list(_INFLIGHT_RESULT.get(normalized_query, []))
        if result or get_cached(normalized_query) is not None:
            return get_cached(normalized_query) or result, "cache_hit"
        return [], "error"

    try:
        results = fetch() or []
        put_cache(normalized_query, results)
        record_usage(user_id)
        with _LOCK:
            _INFLIGHT_RESULT[normalized_query] = list(results)
        return results, "ok"
    except Exception as exc:
        logger.warning("YouTube guarded search failed: %s", type(exc).__name__)
        return [], "error"
    finally:
        with _LOCK:
            ev = _INFLIGHT.pop(normalized_query, None)
            _INFLIGHT_RESULT.pop(normalized_query, None)
            if ev is not None:
                ev.set()
