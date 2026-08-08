"""Single-track reads: basic row, features, and full detail."""

from __future__ import annotations

from typing import Any, Dict, Optional

import duckdb

from app.core.query_helpers import fetch_rows

from .columns import FEATURE_COLS, TRACK_COLS_BASIC
from .queries import map_track_detail_row
from .visibility import is_track_publicly_visible


def get_track_by_id(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    require_public: bool = True,
) -> Optional[Dict[str, Any]]:
    """Load a track row.

    Public consumer reads use ``require_public=True`` (default) so drafts /
    scheduled / suspended / withdrawn stay hidden. Admin mutations must use
    ``require_public=False`` (or ``get_track_by_id_raw``) to avoid false 404s.
    """
    if require_public and not is_track_publicly_visible(conn, track_id):
        return None
    rows, _ = fetch_rows(
        conn, "dim_track",
        columns=TRACK_COLS_BASIC,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None


def get_track_by_id_raw(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """Internal/admin read that ignores public visibility filters."""
    return get_track_by_id(conn, track_id, require_public=False)


def get_track_features(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """
    Return audio features for a track.
    Features are stored in dim_track (no separate fact table needed).
    """
    if not is_track_publicly_visible(conn, track_id):
        return None
    rows, _ = fetch_rows(
        conn, "dim_track",
        columns=FEATURE_COLS,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None


def get_track_detail(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """Full track row with artist, genre, and audio features."""
    if not is_track_publicly_visible(conn, track_id):
        return None
    rows = conn.execute("""
        SELECT
            dt.id_track, dt.spotify_track_id, dt.nombre_track,
            dt.id_artista, dt.id_album, dt.id_genero,
            dt.explicit, dt.duration_ms,
            dt.popularity, dt.danceability, dt.energy, dt.loudness,
            dt.speechiness, dt.acousticness, dt.instrumentalness,
            dt.liveness, dt.valence, dt.tempo,
            da.nombre_artista, dg.nombre_genero
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE dt.id_track = ?
    """, [track_id]).fetchall()
    if not rows:
        return None
    return map_track_detail_row(rows[0])
