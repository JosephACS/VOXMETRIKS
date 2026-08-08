# -*- coding: utf-8 -*-
"""Unified music search: local playable first, optional YouTube Data API fallback."""

from __future__ import annotations

import logging
import re
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from app.core.config import get_settings
from app.core.database import table_exists, transactional
from app.packages.catalog.services.track_source_match import (
    artist_overlap,
    build_identity_from_track,
    build_identity_from_youtube,
    is_incompatible,
    is_strong_match,
    parse_youtube_display,
)
from app.packages.catalog.services.tracks.playback_availability import playable_track_sql
from app.packages.catalog.services.tracks.search import search_tracks
from app.packages.streaming.services.audio.cache import write_cache
from app.packages.streaming.services.audio.models import ResolvedSource
from app.packages.streaming.services.audio.youtube_provider import YouTubeProvider
from app.packages.streaming.services.audio.youtube_search_guard import search_with_guard
from app.packages.streaming.services.audio_source_service import (
    YoutubeProviderUnavailableError,
    persist_validated_youtube_source,
)

logger = logging.getLogger(__name__)

_MIN_LOCAL_HITS = 1

# Soft in-memory adopt validation quotas (atomic under lock).
_ADOPT_USER_MAX_PER_HOUR = 20
_ADOPT_GLOBAL_MAX_PER_HOUR = 150
_ADOPT_WINDOW_SEC = 3600
_adopt_lock = threading.Lock()
_adopt_user_ts: dict[int, list[float]] = defaultdict(list)
_adopt_global_ts: list[float] = []


class TrackSourceMismatchError(Exception):
    """Preferred track is musically incompatible with the selected YouTube source."""

    def __init__(self, message: str, *, can_create_new_track: bool = True):
        super().__init__(message)
        self.code = "TRACK_SOURCE_MISMATCH"
        self.can_create_new_track = can_create_new_track


class AdoptRateLimitError(Exception):
    """Too many new adopt validations in the rolling hour window."""

    code = "adopt_rate_limited"


def clear_adopt_rate_limit_buckets() -> None:
    """Reset adopt validation counters (tests)."""
    with _adopt_lock:
        _adopt_user_ts.clear()
        _adopt_global_ts.clear()


def reserve_adopt_validation_quota(user_id: Optional[int]) -> None:
    """Atomically reserve one adopt-validation slot or raise AdoptRateLimitError.

    Reuse of an already-adopted videoId must not call this.
    """
    now = time.time()
    uid = int(user_id) if user_id is not None else 0
    with _adopt_lock:
        user_bucket = _adopt_user_ts[uid]
        user_bucket[:] = [t for t in user_bucket if now - t < _ADOPT_WINDOW_SEC]
        _adopt_global_ts[:] = [t for t in _adopt_global_ts if now - t < _ADOPT_WINDOW_SEC]
        if len(user_bucket) >= _ADOPT_USER_MAX_PER_HOUR:
            raise AdoptRateLimitError("Adopt validation rate limit exceeded for user")
        if len(_adopt_global_ts) >= _ADOPT_GLOBAL_MAX_PER_HOUR:
            raise AdoptRateLimitError("Adopt validation rate limit exceeded globally")
        user_bucket.append(now)
        _adopt_global_ts.append(now)


def _normalize_query(q: str) -> str:
    s = (q or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b(feat\.?|ft\.?|featuring)\b", " ", s)
    s = re.sub(r"[^\w\sÀ-ÿ]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def music_search(
    conn: duckdb.DuckDBPyConnection,
    q: str,
    *,
    page: int = 1,
    limit: int = 20,
    allow_external: bool = True,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Single search UX:
    1) Local playable tracks
    2) If none adequate → YouTube candidates (not persisted until selected)
    """
    raw = (q or "").strip()
    if len(raw) < 2:
        return {
            "query": raw,
            "phase": "empty",
            "local": {"items": [], "total": 0, "page": page, "limit": limit},
            "external": [],
            "message": "",
            "external_available": bool(get_settings().youtube_api_key.strip()),
        }

    local_items, total, _, _ = search_tracks(
        conn, raw, limit=limit, page=page, playable_only=True
    )
    missing_candidates: List[Dict[str, Any]] = []
    if total == 0:
        all_local, _all_total, _, _ = search_tracks(
            conn, raw, limit=min(10, limit), page=1, playable_only=False
        )
        for row in all_local:
            missing_candidates.append({**row, "playback_status": "missing"})

    if total >= _MIN_LOCAL_HITS:
        return {
            "query": raw,
            "phase": "local",
            "local": {
                "items": [{**i, "playback_status": "playable"} for i in local_items],
                "total": total,
                "page": page,
                "limit": limit,
            },
            "external": [],
            "missing_local": [],
            "message": "",
            "external_available": bool(get_settings().youtube_api_key.strip()),
        }

    external: List[Dict[str, Any]] = []
    phase = "local_empty"
    message = "No encontramos esta canción disponible en VOXMETRIKS."
    if allow_external:
        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            message = "Por ahora solo se muestran resultados disponibles en VOXMETRIKS."
            phase = "external_unavailable"
        else:
            title_hint = missing_candidates[0].get("nombre_track") if missing_candidates else raw
            artist_hint = missing_candidates[0].get("nombre_artista") if missing_candidates else ""
            artists = [a.strip() for a in str(artist_hint or "").split(";") if a.strip()]
            query = raw if not artists else f"{title_hint} {artists[0]}"
            nq = _normalize_query(query)

            def _fetch() -> List[Dict[str, Any]]:
                return YouTubeProvider().search_query_candidates(
                    query,
                    max_results=8,
                    expected_title=str(title_hint or raw),
                    expected_artists=artists,
                )

            external, guard_status = search_with_guard(
                normalized_query=nq,
                user_id=user_id,
                fetch=_fetch,
            )
            if guard_status == "quota_exhausted":
                phase = "external_unavailable"
                message = "Por ahora solo se muestran resultados disponibles en VOXMETRIKS."
                external = []
            elif guard_status == "error":
                phase = "external_error"
                message = "No fue posible buscar esta canción en este momento."
                external = []
            elif external:
                phase = "external"
                message = (
                    "No encontramos esta canción disponible en VOXMETRIKS. "
                    "Estos son resultados encontrados en YouTube."
                )
            else:
                phase = "external_empty"
                message = "No fue posible buscar esta canción en este momento."

    return {
        "query": raw,
        "normalized_query": _normalize_query(raw),
        "phase": phase,
        "local": {"items": [], "total": 0, "page": page, "limit": limit},
        "missing_local": missing_candidates,
        "external": external,
        "message": message,
        "external_available": bool(get_settings().youtube_api_key.strip()),
    }


def _load_track_row(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT dt.id_track, dt.nombre_track, COALESCE(da.nombre_artista, ''),
               dt.duration_ms
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track = ?
        """,
        [int(track_id)],
    ).fetchone()
    if not row:
        return None
    return {
        "id_track": int(row[0]),
        "nombre_track": row[1] or "",
        "nombre_artista": row[2] or "",
        "duration_ms": int(row[3]) if row[3] is not None else None,
    }


def _track_compatible(
    track: Dict[str, Any],
    *,
    yt_title: str,
    yt_channel: str,
    yt_duration_ms: Optional[int],
) -> bool:
    src = build_identity_from_youtube(
        title=yt_title, channel_title=yt_channel, duration_ms=yt_duration_ms
    )
    trg = build_identity_from_track(
        title=str(track.get("nombre_track") or ""),
        artist=str(track.get("nombre_artista") or ""),
        duration_ms=track.get("duration_ms"),
    )
    return is_strong_match(trg, src)


def _find_compatible_track(
    conn: duckdb.DuckDBPyConnection,
    *,
    yt_title: str,
    yt_channel: str,
    yt_duration_ms: Optional[int],
) -> Optional[int]:
    song, artist_guess = parse_youtube_display(yt_title, yt_channel)
    src = build_identity_from_youtube(
        title=yt_title, channel_title=yt_channel, duration_ms=yt_duration_ms
    )
    items, _total, _, _ = search_tracks(
        conn, song[:80] or yt_title[:80], limit=25, page=1, playable_only=False
    )
    strong: List[Tuple[int, bool, float]] = []
    playable = playable_track_sql(conn)
    seen: set[int] = set()

    def _consider(item: Dict[str, Any]) -> None:
        tid = int(item["id_track"])
        if tid in seen:
            return
        if not _track_compatible(
            item, yt_title=yt_title, yt_channel=yt_channel, yt_duration_ms=yt_duration_ms
        ):
            return
        seen.add(tid)
        trg = build_identity_from_track(
            title=str(item.get("nombre_track") or ""),
            artist=str(item.get("nombre_artista") or ""),
            duration_ms=item.get("duration_ms"),
        )
        a_score = artist_overlap(trg, src)
        has_audio = bool(
            conn.execute(
                f"SELECT 1 FROM dim_track dt WHERE dt.id_track = ? AND ({playable})",
                [tid],
            ).fetchone()
        )
        strong.append((tid, has_audio, a_score))

    for item in items:
        _consider(item)
    rows = conn.execute(
        """
        SELECT dt.id_track, dt.nombre_track, COALESCE(da.nombre_artista, ''), dt.duration_ms
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE lower(dt.nombre_track) = lower(?)
        LIMIT 40
        """,
        [song or yt_title],
    ).fetchall()
    for r in rows:
        _consider(
            {
                "id_track": int(r[0]),
                "nombre_track": r[1] or "",
                "nombre_artista": r[2] or "",
                "duration_ms": int(r[3]) if r[3] is not None else None,
            }
        )
    if not strong:
        return None
    strong.sort(key=lambda x: (x[2], 0 if not x[1] else 1), reverse=True)
    best_score = strong[0][2]
    tier = [x for x in strong if x[2] >= best_score - 1e-9]
    for tid, has_audio, _score in tier:
        if not has_audio:
            return tid
    return tier[0][0]


def _create_minimal_track(
    conn: duckdb.DuckDBPyConnection,
    *,
    title: str,
    channel: str,
    duration_ms: Optional[int],
) -> int:
    song, artist_guess = parse_youtube_display(title, channel)
    display_title = song or title or "Untitled"
    display_artist = artist_guess or channel or "Unknown"

    next_id = int(
        conn.execute("SELECT COALESCE(MAX(id_track), 0) + 1 FROM dim_track").fetchone()[0]
    )
    artist_id = None
    if display_artist and table_exists(conn, "dim_artista"):
        arow = conn.execute(
            "SELECT id_artista FROM dim_artista WHERE lower(nombre_artista) = lower(?) LIMIT 1",
            [display_artist],
        ).fetchone()
        if arow:
            artist_id = int(arow[0])
        else:
            artist_id = int(
                conn.execute(
                    "SELECT COALESCE(MAX(id_artista), 0) + 1 FROM dim_artista"
                ).fetchone()[0]
            )
            conn.execute(
                "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (?, ?)",
                [artist_id, display_artist],
            )
    cols = [c[0] for c in conn.execute("DESCRIBE dim_track").fetchall()]
    fields = ["id_track", "nombre_track"]
    vals: List[Any] = [next_id, display_title]
    if "id_artista" in cols and artist_id is not None:
        fields.append("id_artista")
        vals.append(artist_id)
    if "duration_ms" in cols and duration_ms:
        fields.append("duration_ms")
        vals.append(duration_ms)
    placeholders = ", ".join(["?"] * len(fields))
    conn.execute(
        f"INSERT INTO dim_track ({', '.join(fields)}) VALUES ({placeholders})",
        vals,
    )
    return next_id


def _fetch_youtube_meta(video_id: str) -> Dict[str, Any]:
    """Single Data API validation. Raises ValueError or YoutubeProviderUnavailableError."""
    api_key = get_settings().youtube_api_key.strip()
    if not api_key:
        raise YoutubeProviderUnavailableError(
            "YouTube Data API is not configured; video validity is unknown"
        )
    details = YouTubeProvider()._fetch_video_details([video_id], api_key)
    if details is None:
        raise YoutubeProviderUnavailableError(
            "YouTube Data API is unavailable; video validity is unknown"
        )
    if video_id not in details:
        raise ValueError("No se pudo validar el video en YouTube")
    return details[video_id]


def _resolve_track_for_meta(
    conn: duckdb.DuckDBPyConnection,
    meta: Dict[str, Any],
    *,
    preferred_track_id: Optional[int],
    require_preferred: bool,
) -> Tuple[int, bool, bool]:
    """Return (track_id, created, preferred_rejected). May create artist/track."""
    title = (meta.get("title") or "Untitled").strip()
    channel = (meta.get("channel_title") or "").strip()
    duration_ms = int(meta.get("duration_sec") or 0) * 1000 or None
    src_id = build_identity_from_youtube(
        title=title, channel_title=channel, duration_ms=duration_ms
    )
    preferred_rejected = False
    track_id: Optional[int] = None
    created = False

    if preferred_track_id is not None:
        preferred = _load_track_row(conn, int(preferred_track_id))
        if preferred:
            pref_id = build_identity_from_track(
                title=preferred["nombre_track"],
                artist=preferred["nombre_artista"],
                duration_ms=preferred.get("duration_ms"),
            )
            if is_strong_match(pref_id, src_id):
                track_id = int(preferred["id_track"])
            elif is_incompatible(pref_id, src_id) or not is_strong_match(pref_id, src_id):
                if require_preferred:
                    raise TrackSourceMismatchError(
                        "La fuente seleccionada no corresponde a la canción existente.",
                        can_create_new_track=True,
                    )
                preferred_rejected = True
                track_id = None

    if track_id is None:
        track_id = _find_compatible_track(
            conn, yt_title=title, yt_channel=channel, yt_duration_ms=duration_ms
        )

    if track_id is None:
        track_id = _create_minimal_track(
            conn, title=title, channel=channel, duration_ms=duration_ms
        )
        created = True

    return int(track_id), created, preferred_rejected


def _persist_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    video_id: str,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    title = (meta.get("title") or "").strip()
    channel = (meta.get("channel_title") or "").strip()
    out = persist_validated_youtube_source(
        conn,
        int(track_id),
        video_id=video_id,
        query=f"{title} {channel}".strip() or f"adopt:{video_id}",
    )
    if out is None:
        # Track may exist without warehouse context columns; write cache directly.
        write_cache(
            conn,
            ResolvedSource(
                track_id=int(track_id),
                provider="youtube",
                status="ok",
                source_ref=video_id,
                youtube_video_id=video_id,
                query=f"adopt:{video_id}",
                confidence_score=1.0,
            ),
        )
        out = {
            "track_id": int(track_id),
            "provider": "youtube",
            "youtube_video_id": video_id,
            "source_ref": video_id,
            "status": "ok",
        }
    return out


def _reuse_adopted_source(
    conn: duckdb.DuckDBPyConnection,
    *,
    vid: str,
    preferred_track_id: Optional[int],
    require_preferred: bool,
) -> Optional[Dict[str, Any]]:
    """Return reuse payload if ``vid`` is already associated; else None."""
    if not table_exists(conn, "app_track_audio_source"):
        return None
    row = conn.execute(
        """
        SELECT track_id FROM app_track_audio_source
        WHERE youtube_video_id = ? OR source_ref = ?
        LIMIT 1
        """,
        [vid, vid],
    ).fetchone()
    if not row:
        return None
    tid = int(row[0])
    preferred_rejected = False
    if preferred_track_id is not None and int(preferred_track_id) != tid:
        if require_preferred:
            raise TrackSourceMismatchError(
                "La fuente seleccionada ya está asociada a otra canción.",
                can_create_new_track=False,
            )
        preferred_rejected = True
    return {
        "track_id": tid,
        "created": False,
        "reused_source": True,
        "video_id": vid,
        "preferred_rejected": preferred_rejected,
    }


def adopt_youtube_result(
    conn: duckdb.DuckDBPyConnection,
    *,
    video_id: str,
    preferred_track_id: Optional[int] = None,
    require_preferred: bool = False,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate videoId via Data API once, then attach in a single DuckDB transaction
    (artist/track/source). Never stores audiovisual files.

    ``preferred_track_id`` is a suggestion only. Incompatible preferences are
    rejected (when ``require_preferred``) or ignored in favour of a compatible
    Track / new Track.
    """
    vid = (video_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        raise ValueError("videoId inválido")

    # Fast path: reuse existing source — never silently rebind; no quota burn.
    reused = _reuse_adopted_source(
        conn,
        vid=vid,
        preferred_track_id=preferred_track_id,
        require_preferred=require_preferred,
    )
    if reused is not None:
        return reused

    # Quota for *new* validations only (atomic check+record).
    reserve_adopt_validation_quota(user_id)

    # Validate once outside the write transaction (network I/O).
    meta = _fetch_youtube_meta(vid)
    title = (meta.get("title") or "Untitled").strip()
    channel = (meta.get("channel_title") or "").strip()
    duration_ms = int(meta.get("duration_sec") or 0) * 1000 or None

    with transactional(conn):
        # Concurrent same-video adopts: winner associates once; loser reuses.
        reused = _reuse_adopted_source(
            conn,
            vid=vid,
            preferred_track_id=preferred_track_id,
            require_preferred=require_preferred,
        )
        if reused is not None:
            return reused

        track_id, created, preferred_rejected = _resolve_track_for_meta(
            conn,
            meta,
            preferred_track_id=preferred_track_id,
            require_preferred=require_preferred,
        )
        out = _persist_source(conn, track_id, vid, meta)

    song, artist_guess = parse_youtube_display(title, channel)
    return {
        "track_id": int(track_id),
        "created": created,
        "reused_source": False,
        "video_id": vid,
        "title": song or title,
        "channel_title": channel,
        "artist": artist_guess or channel,
        "duration_ms": duration_ms,
        "thumbnail": meta.get("thumbnail") or "",
        "audio_source": out,
        "preferred_rejected": preferred_rejected,
    }


def repair_youtube_source_association(
    conn: duckdb.DuckDBPyConnection,
    *,
    video_id: str,
) -> Dict[str, Any]:
    """
    Validate first, then detach a YouTube source from an incompatible Track and
    re-attach to a compatible Track (or create one) in one transaction.
    """
    vid = (video_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        raise ValueError("videoId inválido")
    if not table_exists(conn, "app_track_audio_source"):
        raise ValueError("Tabla de fuentes no disponible")

    row = conn.execute(
        """
        SELECT track_id FROM app_track_audio_source
        WHERE youtube_video_id = ? OR source_ref = ?
        LIMIT 1
        """,
        [vid, vid],
    ).fetchone()
    if not row:
        return adopt_youtube_result(conn, video_id=vid)

    old_tid = int(row[0])
    old_track = _load_track_row(conn, old_tid)
    meta = _fetch_youtube_meta(vid)
    title = (meta.get("title") or "").strip()
    channel = (meta.get("channel_title") or "").strip()
    duration_ms = int(meta.get("duration_sec") or 0) * 1000 or None

    if old_track and _track_compatible(
        old_track, yt_title=title, yt_channel=channel, yt_duration_ms=duration_ms
    ):
        return {
            "ok": True,
            "action": "unchanged",
            "track_id": old_tid,
            "video_id": vid,
            "title": title,
        }

    with transactional(conn):
        conn.execute(
            "DELETE FROM app_track_audio_source WHERE track_id = ? AND (youtube_video_id = ? OR source_ref = ?)",
            [old_tid, vid, vid],
        )
        track_id, created, _ = _resolve_track_for_meta(
            conn,
            meta,
            preferred_track_id=None,
            require_preferred=False,
        )
        _persist_source(conn, track_id, vid, meta)

    return {
        "ok": True,
        "action": "reassigned",
        "previous_track_id": old_tid,
        "previous_track_title": (old_track or {}).get("nombre_track"),
        "track_id": track_id,
        "created": created,
        "video_id": vid,
        "title": parse_youtube_display(title, channel)[0] or title,
        "channel_title": channel,
    }
