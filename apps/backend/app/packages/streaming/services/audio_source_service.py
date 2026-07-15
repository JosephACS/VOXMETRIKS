"""Resolve playable audio sources for catalog tracks (multi-provider).

Results are cached in ``app_track_audio_source``. The frontend plays via
YouTube IFrame, HTML5 stream URLs (Audius), or local demo fallback.
We never download or re-host copyrighted audio.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

import duckdb

from app.core.database import using_write_conn

from .audio.cache import (
    STATUS_DISABLED,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_OK,
    STATUS_PENDING,
    is_cache_usable,
    mark_failure,
    migrate_audio_source_columns,
    read_cache,
)
from .audio.resolver import get_audio_resolver
from .audio.youtube_scoring import (
    build_search_query,
    parse_iso8601_duration,
    pick_best_youtube_candidate,
    score_youtube_candidate,
)

logger = logging.getLogger(__name__)

# Re-export for tests and legacy imports
__all__ = [
    "STATUS_OK",
    "STATUS_NOT_FOUND",
    "STATUS_DISABLED",
    "STATUS_ERROR",
    "STATUS_PENDING",
    "parse_iso8601_duration",
    "score_youtube_candidate",
    "pick_best_youtube_candidate",
    "get_audio_source_response",
    "resolve_audio_source",
    "report_source_failure",
]

_scheduled_lock = threading.Lock()
_scheduled_ids: set[int] = set()


def _schedule_resolve(track_id: int, skip_provider: Optional[str] = None) -> None:
    with _scheduled_lock:
        if track_id in _scheduled_ids:
            return
        _scheduled_ids.add(track_id)

    def _job() -> None:
        try:
            # Do not hold using_write_conn across YouTube/Audius network I/O —
            # that blocked the shared DuckDB lock and starved Home API reads.
            get_audio_resolver().resolve_background(
                track_id, force=False, skip_provider=skip_provider
            )
        except Exception:
            logger.exception("background audio resolve failed track_id=%s", track_id)
        finally:
            with _scheduled_lock:
                _scheduled_ids.discard(track_id)

    threading.Thread(
        target=_job, daemon=True, name=f"audio-resolve-{track_id}"
    ).start()


def get_audio_source_response(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
    async_resolve: bool = True,
    skip_provider: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return cached audio source or schedule background resolution on miss.

    Priority 1: ``local_published`` (Spec 031) — never overwrite with YouTube/Audius.
    """
    migrate_audio_source_columns(conn)

    # Prefer local_published before warehouse context (demo synthetic tracks).
    cached = read_cache(conn, track_id)
    if cached and cached.get("provider") == "local_published":
        return _api_dict(cached)

    from .audio.resolver import build_track_context

    ctx = build_track_context(conn, track_id)
    if ctx is None:
        return None

    query = build_search_query(ctx.track_name, ctx.artist_name)

    if not force:
        if cached and is_cache_usable(cached):
            return _api_dict(cached)

    if async_resolve and not force:
        _schedule_resolve(track_id, skip_provider=skip_provider)
        return {
            "track_id": track_id,
            "provider": "pending",
            "youtube_video_id": None,
            "source_ref": None,
            "playable_url": None,
            "query": query,
            "status": STATUS_PENDING,
            "confidence_score": None,
        }

    with using_write_conn() as write_conn:
        migrate_audio_source_columns(write_conn)
        # Re-check local_published under write conn
        cached_w = read_cache(write_conn, track_id)
        if cached_w and cached_w.get("provider") == "local_published":
            return _api_dict(cached_w)
        return resolve_audio_source(
            write_conn, track_id, force=force, skip_provider=skip_provider
        )


def resolve_audio_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
    skip_provider: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) the best playable source for a track."""
    migrate_audio_source_columns(conn)
    resolver = get_audio_resolver()
    result = resolver.resolve(
        conn, track_id, force=force, skip_provider=skip_provider
    )
    if result is None:
        return None
    if result.status == STATUS_ERROR:
        return result.to_api_dict()
    return result.to_api_dict()


def report_source_failure(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> None:
    """Increment failure count when frontend playback fails."""
    migrate_audio_source_columns(conn)
    mark_failure(conn, track_id)


def _api_dict(cached: dict) -> dict:
    return {
        "track_id": int(cached["track_id"]),
        "provider": cached["provider"],
        "youtube_video_id": cached.get("youtube_video_id"),
        "source_ref": cached.get("source_ref"),
        "playable_url": cached.get("playable_url"),
        "query": cached.get("query"),
        "status": cached["status"],
        "confidence_score": cached.get("confidence_score"),
    }
