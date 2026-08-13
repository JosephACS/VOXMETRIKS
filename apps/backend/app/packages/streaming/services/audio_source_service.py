"""Resolve playable audio sources for catalog tracks (multi-provider).

Results are cached in ``app_track_audio_source``. The frontend plays via
YouTube IFrame, HTML5 stream URLs (Audius), or local demo fallback.
We never download or re-host copyrighted audio.
"""

from __future__ import annotations

import logging
import re
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
    write_cache,
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
    "list_unresolved_audio",
    "search_audio_candidates",
    "save_manual_youtube_source",
    "persist_validated_youtube_source",
    "validate_youtube_video_id",
    "YoutubeProviderUnavailableError",
    "mark_audio_unavailable",
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
    exclude_source_ref: Optional[str] = None,
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

    ctx = build_track_context(
        conn,
        track_id,
        exclude_source_refs=(
            {part.strip() for part in str(exclude_source_ref).split(",") if part.strip()}
            if exclude_source_ref
            else None
        ),
    )
    if ctx is None:
        return None

    query = build_search_query(ctx.track_name, ctx.artist_name)

    if not force:
        if cached and is_cache_usable(cached):
            cached_ref = cached.get("youtube_video_id") or cached.get("source_ref")
            excluded = {
                part.strip()
                for part in str(exclude_source_ref or "").split(",")
                if part.strip()
            }
            if not (excluded and cached_ref in excluded):
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
            write_conn,
            track_id,
            force=force,
            skip_provider=skip_provider,
            exclude_source_ref=exclude_source_ref,
        )


def resolve_audio_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
    skip_provider: Optional[str] = None,
    exclude_source_ref: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) the best playable source for a track."""
    migrate_audio_source_columns(conn)
    resolver = get_audio_resolver()
    result = resolver.resolve(
        conn,
        track_id,
        force=force,
        skip_provider=skip_provider,
        exclude_source_ref=exclude_source_ref,
    )
    if result is None:
        return None
    if result.status == STATUS_ERROR:
        return result.to_api_dict()
    return result.to_api_dict()


def report_source_failure(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> None:
    """Increment failure count when frontend playback fails.

    Also warm ranked YouTube alternates so the immediate exclude/fallback
    request can reuse candidates without a second flaky Data API search.
    """
    migrate_audio_source_columns(conn)
    mark_failure(conn, track_id)
    cached = read_cache(conn, track_id)
    if not cached or cached.get("provider") != "youtube":
        return
    from .audio.resolver import build_track_context
    from .audio.youtube_provider import YouTubeProvider, _ALTERNATE_IDS

    if _ALTERNATE_IDS.get(track_id):
        return
    ctx = build_track_context(conn, track_id)
    if ctx is None:
        return
    try:
        YouTubeProvider().warm_alternates(ctx)
    except Exception:  # noqa: BLE001 — warming must not break failure reporting
        logger.exception("Failed warming YouTube alternates for track %s", track_id)


def list_unresolved_audio(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int = 50,
    offset: int = 0,
    q: Optional[str] = None,
) -> Dict[str, Any]:
    """Admin tray: tracks whose external audio is not_found / error / disabled."""
    migrate_audio_source_columns(conn)
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    params: list[Any] = []
    where = "s.status IN ('not_found', 'error', 'disabled')"
    if q and q.strip():
        where += (
            " AND (LOWER(COALESCE(t.nombre_track, '')) LIKE ? "
            "OR LOWER(COALESCE(a.nombre_artista, '')) LIKE ? "
            "OR CAST(s.track_id AS VARCHAR) = ?)"
        )
        like = f"%{q.strip().lower()}%"
        params.extend([like, like, q.strip()])
    params.extend([limit, offset])
    rows = conn.execute(
        f"""
        SELECT s.track_id, s.provider, s.status, s.query, s.resolved_at,
               s.failure_count, t.nombre_track, a.nombre_artista, t.duration_ms
        FROM app_track_audio_source s
        LEFT JOIN dim_track t ON t.id_track = s.track_id
        LEFT JOIN dim_artista a ON a.id_artista = t.id_artista
        WHERE {where}
          AND COALESCE(s.provider, '') <> 'local_published'
        ORDER BY s.resolved_at DESC NULLS LAST, s.track_id DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()
    items = [
        {
            "track_id": int(r[0]),
            "provider": r[1],
            "status": r[2],
            "query": r[3],
            "resolved_at": r[4].isoformat() if r[4] is not None else None,
            "failure_count": int(r[5] or 0),
            "track_name": r[6],
            "artist_name": r[7],
            "duration_ms": int(r[8]) if r[8] is not None else None,
        }
        for r in rows
    ]
    count_params = params[:-2] if q and q.strip() else []
    count_where = "s.status IN ('not_found', 'error', 'disabled')"
    if q and q.strip():
        count_where += (
            " AND (LOWER(COALESCE(t.nombre_track, '')) LIKE ? "
            "OR LOWER(COALESCE(a.nombre_artista, '')) LIKE ? "
            "OR CAST(s.track_id AS VARCHAR) = ?)"
        )
    total = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM app_track_audio_source s
        LEFT JOIN dim_track t ON t.id_track = s.track_id
        LEFT JOIN dim_artista a ON a.id_artista = t.id_artista
        WHERE {count_where}
          AND COALESCE(s.provider, '') <> 'local_published'
        """,
        count_params,
    ).fetchone()[0]
    return {"items": items, "total": int(total), "limit": limit, "offset": offset}


def search_audio_candidates(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """Admin: live-search candidates without writing cache."""
    from .audio.resolver import build_track_context
    from .audio.youtube_provider import YouTubeProvider

    ctx = build_track_context(conn, track_id)
    if ctx is None:
        return None
    candidates = YouTubeProvider().search_candidates(ctx)
    return {
        "track_id": track_id,
        "track_name": ctx.track_name,
        "artist_name": ctx.artist_name,
        "duration_ms": ctx.duration_ms,
        "candidates": candidates,
    }


def save_manual_youtube_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    video_id_or_url: str,
) -> Optional[Dict[str, Any]]:
    """Admin: paste YouTube URL/ID, always validate via Data API, cache as ok.

    Callers that already validated should use ``persist_validated_youtube_source``.
    """
    from .audio.metadata_normalize import extract_youtube_video_id
    from .audio.models import ResolvedSource
    from .audio.resolver import build_track_context

    migrate_audio_source_columns(conn)
    existing = read_cache(conn, track_id)
    if existing and existing.get("provider") == "local_published":
        return _api_dict(existing)

    ctx = build_track_context(conn, track_id)
    if ctx is None:
        return None

    video_id = extract_youtube_video_id(video_id_or_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL or video ID")

    outcome = validate_youtube_video_id(video_id)
    if outcome == "invalid":
        raise ValueError("YouTube video is unavailable or invalid")
    if outcome == "provider_unavailable":
        raise YoutubeProviderUnavailableError(
            "YouTube Data API is unavailable; video validity is unknown"
        )

    resolved = ResolvedSource(
        track_id=track_id,
        provider="youtube",
        status=STATUS_OK,
        source_ref=video_id,
        youtube_video_id=video_id,
        query=f"manual:{video_id}",
        confidence_score=1.0,
    )
    write_cache(conn, resolved)
    return resolved.to_api_dict()


def persist_validated_youtube_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    video_id: str,
    query: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Persist a YouTube source that was already validated via Data API."""
    from .audio.models import ResolvedSource
    from .audio.resolver import build_track_context

    migrate_audio_source_columns(conn)
    existing = read_cache(conn, track_id)
    if existing and existing.get("provider") == "local_published":
        return _api_dict(existing)
    if build_track_context(conn, track_id) is None:
        return None
    vid = (video_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        raise ValueError("Invalid YouTube URL or video ID")
    resolved = ResolvedSource(
        track_id=track_id,
        provider="youtube",
        status=STATUS_OK,
        source_ref=vid,
        youtube_video_id=vid,
        query=query or f"manual:{vid}",
        confidence_score=1.0,
    )
    write_cache(conn, resolved)
    return resolved.to_api_dict()


class YoutubeProviderUnavailableError(Exception):
    """Raised when YouTube validity cannot be determined (no key / API failure)."""

    code = "provider_unavailable"


def mark_audio_unavailable(
    conn: duckdb.DuckDBPyConnection, track_id: int, *, reason: str = "manual"
) -> Optional[Dict[str, Any]]:
    """Admin: explicitly mark track as not_found (never touches local_published)."""
    from .audio.models import ResolvedSource
    from .audio.resolver import build_track_context

    migrate_audio_source_columns(conn)
    existing = read_cache(conn, track_id)
    if existing and existing.get("provider") == "local_published":
        return _api_dict(existing)
    ctx = build_track_context(conn, track_id)
    if ctx is None:
        return None
    resolved = ResolvedSource(
        track_id=track_id,
        provider="youtube",
        status=STATUS_NOT_FOUND,
        query=f"unavailable:{reason}",
        confidence_score=0.0,
    )
    write_cache(conn, resolved)
    return resolved.to_api_dict()


def validate_youtube_video_id(video_id: str) -> str:
    """Validate via YouTube Data API only (no oEmbed).

    Returns one of: ``valid``, ``invalid``, ``provider_unavailable``.
    Never treats provider failure as a known-invalid video.
    """
    vid = (video_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        return "invalid"
    try:
        from app.core.config import get_settings

        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            return "provider_unavailable"
        import httpx

        r = httpx.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "status,contentDetails",
                "id": vid,
                "key": api_key,
            },
            timeout=8.0,
        )
        if r.status_code != 200:
            return "provider_unavailable"
        items = (r.json() or {}).get("items") or []
        if not items:
            return "invalid"
        status = items[0].get("status") or {}
        if status.get("privacyStatus") not in (None, "public", "unlisted"):
            return "invalid"
        if status.get("embeddable") is False:
            return "invalid"
        return "valid"
    except Exception:
        return "provider_unavailable"


def _validate_youtube_video_id(video_id: str) -> bool:
    """Legacy bool adapter for tests. Provider unavailable → False (not valid).

    Prefer ``validate_youtube_video_id`` for coherent HTTP mapping.
    """
    return validate_youtube_video_id(video_id) == "valid"


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
