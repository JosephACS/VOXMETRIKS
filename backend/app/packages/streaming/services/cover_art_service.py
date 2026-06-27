"""Resolve real cover-art image URLs for catalog tracks via the iTunes Search API.

The iTunes Search API is free and needs no API key. We never re-host images; we
store the resolved artwork URL (Apple CDN) and let the browser load it, with a
gradient fallback in the UI. Results are cached in ``app_track_cover`` so each
track is looked up only once.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import duckdb
import httpx

from app.core.time_util import utc_now

logger = logging.getLogger(__name__)

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
_REQUEST_TIMEOUT = 8.0

STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"

# iTunes returns 100x100 artwork; bump to a crisp square for the UI.
_ARTWORK_SRC = "100x100bb"
_ARTWORK_DST = "600x600bb"


def _track_terms(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[str]:
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
    artist_name = (row[1] or "").strip()
    if not track_name:
        return None
    return f"{track_name} {artist_name}".strip()


def _read_cache(conn: duckdb.DuckDBPyConnection, track_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT track_id, image_url, status FROM app_track_cover WHERE track_id = ?",
        [track_id],
    ).fetchone()
    if not row:
        return None
    return {"track_id": int(row[0]), "image_url": row[1], "status": row[2]}


def _write_cache(
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


def upscale_artwork(url: str) -> str:
    """Replace the small 100x100 artwork with a larger square variant."""
    if not url:
        return url
    return url.replace(_ARTWORK_SRC, _ARTWORK_DST)


def _search_itunes(terms: str) -> Optional[str]:
    params = {
        "term": terms,
        "media": "music",
        "entity": "song",
        "limit": "1",
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

    artwork = results[0].get("artworkUrl100") or results[0].get("artworkUrl60")
    if not artwork:
        return None
    return upscale_artwork(artwork)


def resolve_cover(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) a cover image URL for a track.

    Returns ``{track_id, image_url, status}`` or ``None`` if the track does not
    exist.
    """
    terms = _track_terms(conn, track_id)
    if terms is None:
        return None

    if not force:
        cached = _read_cache(conn, track_id)
        if cached and cached["status"] in (STATUS_OK, STATUS_NOT_FOUND):
            return cached

    image_url = _search_itunes(terms)
    status = STATUS_OK if image_url else STATUS_NOT_FOUND
    _write_cache(conn, track_id, image_url, status)
    return {"track_id": track_id, "image_url": image_url, "status": status}
