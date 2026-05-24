"""backend/services/track_service.py"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows

_TRACK_COLS = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero", "explicit", "duration_ms",
]

_FACT_COLS = [
    "id_fact", "id_track", "popularity",
    "danceability", "energy", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
    "key_col", "mode_col", "time_signature",
]


def get_tracks(
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    artist_id: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * limit

    conditions: List[str] = []
    params: List[Any] = []

    if search:
        conditions.append("LOWER(nombre_track) LIKE LOWER(?)")
        params.append(f"%{search}%")
    if genre_id is not None:
        conditions.append("id_genero = ?")
        params.append(genre_id)
    if artist_id is not None:
        conditions.append("id_artista = ?")
        params.append(artist_id)

    where = " AND ".join(conditions)

    rows, _ = fetch_rows(
        conn, "dim_track",
        columns=_TRACK_COLS,
        where=where,
        order_by="nombre_track",
        limit=limit,
        offset=offset,
        params=params,
    )
    total = count_rows(conn, "dim_track", where=where, params=params)
    return rows, total


def get_track_by_id(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "dim_track",
        columns=_TRACK_COLS,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None


def get_track_features(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "fact_audio_features",
        columns=_FACT_COLS,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None
