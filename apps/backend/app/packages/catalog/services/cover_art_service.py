"""Resolve source-bound or catalog cover-art image URLs for tracks.

The iTunes Search API is free and needs no API key. We never re-host images; we
store the resolved artwork URL (Apple CDN) and let the browser load it, with a
gradient fallback in the UI. Results are cached in ``app_track_cover`` /
``app_artist_cover`` so each entity is looked up only once.

Resolution order for tracks:
  1. iTunes song search (track + artist)
  2. iTunes song search (track only)
  3. iTunes artist search (primary artist name)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import duckdb
import httpx

from app.core.time_util import utc_now

logger = logging.getLogger(__name__)

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
_REQUEST_TIMEOUT = 8.0

STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"

_ARTWORK_SRC = "100x100bb"
_ARTWORK_DST = "600x600bb"


def upscale_artwork(url: str) -> str:
    """Replace the small 100x100 artwork with a larger square variant."""
    if not url:
        return url
    return url.replace(_ARTWORK_SRC, _ARTWORK_DST)


def _track_row(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Tuple[str, str]]:
    row = conn.execute(
        """
        SELECT dt.nombre_track, da.nombre_artista
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track = ?
        """,
        [track_id],
    ).fetchone()
    if not row:
        return None
    track_name = (row[0] or "").strip()
    artist_raw = (row[1] or "").strip()
    artist_name = artist_raw.split(";")[0].strip() if artist_raw else ""
    if not track_name:
        return None
    return track_name, artist_name


def _artist_name(conn: duckdb.DuckDBPyConnection, artist_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT nombre_artista FROM dim_artista WHERE id_artista = ?",
        [artist_id],
    ).fetchone()
    if not row or not row[0]:
        return None
    raw = str(row[0]).strip()
    return raw.split(";")[0].strip() or None


def _read_track_cache(conn: duckdb.DuckDBPyConnection, track_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT track_id, image_url, status, resolved_at FROM app_track_cover WHERE track_id = ?",
        [track_id],
    ).fetchone()
    if not row:
        return None
    return {
        "track_id": int(row[0]),
        "image_url": row[1],
        "status": row[2],
        "resolved_at": row[3],
    }


def _cache_is_fresh(cached: Dict[str, Any]) -> bool:
    """Keep successful hits forever; retry not_found after a configurable TTL."""
    status = cached.get("status")
    if status == STATUS_OK and cached.get("image_url"):
        return True
    if status != STATUS_NOT_FOUND:
        return False
    resolved_at = cached.get("resolved_at")
    if resolved_at is None:
        return False
    try:
        from datetime import timezone

        from app.core.config import get_settings

        if getattr(resolved_at, "tzinfo", None) is None:
            resolved_at = resolved_at.replace(tzinfo=timezone.utc)
        ttl = float(get_settings().cover_not_found_ttl_sec)
        age = (utc_now() - resolved_at).total_seconds()
        return age < ttl
    except Exception:
        return False


def _write_track_cache(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    image_url: Optional[str],
    status: str,
) -> None:
    conn.execute("DELETE FROM app_track_cover WHERE track_id = ?", [track_id])
    conn.execute(
        """
        INSERT INTO app_track_cover (track_id, image_url, status, resolved_at)
        VALUES (?, ?, ?, ?)
        """,
        [track_id, image_url, status, utc_now()],
    )


def _read_artist_cache(conn: duckdb.DuckDBPyConnection, artist_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT artist_id, image_url, status, resolved_at FROM app_artist_cover WHERE artist_id = ?",
        [artist_id],
    ).fetchone()
    if not row:
        return None
    return {
        "artist_id": int(row[0]),
        "image_url": row[1],
        "status": row[2],
        "resolved_at": row[3],
    }


def _write_artist_cache(
    conn: duckdb.DuckDBPyConnection,
    artist_id: int,
    image_url: Optional[str],
    status: str,
) -> None:
    conn.execute("DELETE FROM app_artist_cover WHERE artist_id = ?", [artist_id])
    conn.execute(
        """
        INSERT INTO app_artist_cover (artist_id, image_url, status, resolved_at)
        VALUES (?, ?, ?, ?)
        """,
        [artist_id, image_url, status, utc_now()],
    )


def _itunes_search(terms: str, *, entity: str = "song", limit: int = 1) -> Optional[str]:
    params = {
        "term": terms,
        "media": "music",
        "entity": entity,
        "limit": str(limit),
    }
    try:
        resp = httpx.get(_ITUNES_SEARCH_URL, params=params, timeout=_REQUEST_TIMEOUT)
    except httpx.HTTPError as exc:
        logger.warning("iTunes search request failed: %s", exc)
        return None

    if resp.status_code != 200:
        logger.warning("iTunes search returned %s", resp.status_code)
        return None

    try:
        results = resp.json().get("results") or []
    except ValueError:
        return None
    if not results:
        return None

    hit = results[0]
    artwork = hit.get("artworkUrl100") or hit.get("artworkUrl60")
    if not artwork:
        return None
    return upscale_artwork(artwork)


def _resolve_track_image(track_name: str, artist_name: str) -> Optional[str]:
    if artist_name:
        url = _itunes_search(f"{track_name} {artist_name}", entity="song")
        if url:
            return url
    url = _itunes_search(track_name, entity="song")
    if url:
        return url
    if artist_name:
        return _itunes_search(artist_name, entity="musicArtist")
    return None


def get_cached_cover(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """Return cached cover row when present and still fresh."""
    cached = _read_track_cache(conn, track_id)
    if cached and _cache_is_fresh(cached):
        return {"track_id": cached["track_id"], "image_url": cached["image_url"], "status": cached["status"]}
    return None


def get_cached_artist_cover(
    conn: duckdb.DuckDBPyConnection, artist_id: int
) -> Optional[Dict[str, Any]]:
    cached = _read_artist_cache(conn, artist_id)
    if cached and _cache_is_fresh(cached):
        return {
            "artist_id": cached["artist_id"],
            "image_url": cached["image_url"],
            "status": cached["status"],
        }
    return None


def cover_urls_for_tracks(
    conn: duckdb.DuckDBPyConnection, track_ids: list[int]
) -> Dict[int, str]:
    """Bulk read of OK cover URLs for home/smart feeds (no network)."""
    ids = [int(t) for t in track_ids if t is not None]
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT track_id, image_url
        FROM app_track_cover
        WHERE status = '{STATUS_OK}'
          AND image_url IS NOT NULL
          AND track_id IN ({placeholders})
        """,
        ids,
    ).fetchall()
    covers = {int(r[0]): str(r[1]) for r in rows if r[1]}
    # Artwork is catalog-owned; do not derive covers from external player
    # sources, which may be stale or point at a different recording.
    return covers


def resolve_cover(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) a cover image URL for a track."""
    row = _track_row(conn, track_id)
    if row is None:
        return None
    track_name, artist_name = row

    if not force:
        cached = _read_track_cache(conn, track_id)
        if cached and _cache_is_fresh(cached):
            return {
                "track_id": cached["track_id"],
                "image_url": cached["image_url"],
                "status": cached["status"],
            }

    image_url = _resolve_track_image(track_name, artist_name)
    status = STATUS_OK if image_url else STATUS_NOT_FOUND
    _write_track_cache(conn, track_id, image_url, status)
    return {"track_id": track_id, "image_url": image_url, "status": status}


def resolve_artist_cover(
    conn: duckdb.DuckDBPyConnection,
    artist_id: int,
    *,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) a portrait/artwork URL for an artist."""
    name = _artist_name(conn, artist_id)
    if name is None:
        return None

    if not force:
        cached = _read_artist_cache(conn, artist_id)
        if cached and _cache_is_fresh(cached):
            return {
                "artist_id": cached["artist_id"],
                "image_url": cached["image_url"],
                "status": cached["status"],
            }

    image_url = _itunes_search(name, entity="musicArtist")
    status = STATUS_OK if image_url else STATUS_NOT_FOUND
    _write_artist_cache(conn, artist_id, image_url, status)
    return {"artist_id": artist_id, "image_url": image_url, "status": status}

