"""backend/services/track_service.py"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows

# All audio features are now stored directly in dim_track
_TRACK_COLS = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero", "explicit", "duration_ms",
    "danceability", "energy", "loudness", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo", "popularity",
]

_TRACK_COLS_BASIC = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero", "explicit", "duration_ms",
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
        columns=_TRACK_COLS_BASIC,
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
        columns=_TRACK_COLS_BASIC,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None


def get_track_features(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """
    Return audio features for a track.
    Features are stored in dim_track (no separate fact table needed).
    """
    feature_cols = [
        "id_track", "popularity", "danceability", "energy", "loudness",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo",
    ]
    rows, _ = fetch_rows(
        conn, "dim_track",
        columns=feature_cols,
        where="id_track = ?",
        params=[track_id],
    )
    return rows[0] if rows else None


def create_track(
    conn: duckdb.DuckDBPyConnection,
    nombre_track: str,
    spotify_track_id: Optional[str] = None,
    id_artista: Optional[int] = None,
    id_album: Optional[int] = None,
    id_genero: Optional[int] = None,
    explicit: Optional[bool] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    row = conn.execute("SELECT COALESCE(MAX(id_track), 0) + 1 FROM dim_track").fetchone()
    new_id = row[0]
    conn.execute(
        """INSERT INTO dim_track
           (id_track, spotify_track_id, nombre_track, id_artista, id_album,
            id_genero, explicit, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [new_id, spotify_track_id, nombre_track.strip(),
         id_artista, id_album, id_genero, explicit, duration_ms]
    )
    return {
        "id_track":         new_id,
        "spotify_track_id": spotify_track_id,
        "nombre_track":     nombre_track.strip(),
        "id_artista":       id_artista,
        "id_album":         id_album,
        "id_genero":        id_genero,
        "explicit":         explicit,
        "duration_ms":      duration_ms,
    }


def update_track(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    nombre_track: Optional[str] = None,
    spotify_track_id: Optional[str] = None,
    id_artista: Optional[int] = None,
    id_album: Optional[int] = None,
    id_genero: Optional[int] = None,
    explicit: Optional[bool] = None,
    duration_ms: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    existing = get_track_by_id(conn, track_id)
    if not existing:
        return None

    updates = []
    params = []

    if nombre_track is not None:
        updates.append("nombre_track = ?")
        params.append(nombre_track.strip())
    if spotify_track_id is not None:
        updates.append("spotify_track_id = ?")
        params.append(spotify_track_id)
    if id_artista is not None:
        updates.append("id_artista = ?")
        params.append(id_artista)
    if id_album is not None:
        updates.append("id_album = ?")
        params.append(id_album)
    if id_genero is not None:
        updates.append("id_genero = ?")
        params.append(id_genero)
    if explicit is not None:
        updates.append("explicit = ?")
        params.append(explicit)
    if duration_ms is not None:
        updates.append("duration_ms = ?")
        params.append(duration_ms)

    if not updates:
        return existing

    params.append(track_id)
    conn.execute(
        f"UPDATE dim_track SET {', '.join(updates)} WHERE id_track = ?",
        params
    )
    return get_track_by_id(conn, track_id)


def delete_track(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> bool:
    existing = get_track_by_id(conn, track_id)
    if not existing:
        return False
    conn.execute("DELETE FROM dim_track WHERE id_track = ?", [track_id])
    return True


def search_tracks(
    conn: duckdb.DuckDBPyConnection,
    q: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Search tracks by track name, artist name, or genre name."""
    pattern = f"%{q.strip()}%"
    rows = conn.execute("""
        SELECT
            dt.id_track, dt.spotify_track_id, dt.nombre_track,
            dt.id_artista, dt.id_album, dt.id_genero,
            dt.explicit, dt.duration_ms, dt.popularity,
            da.nombre_artista, dg.nombre_genero
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE LOWER(dt.nombre_track) LIKE LOWER(?)
           OR LOWER(da.nombre_artista) LIKE LOWER(?)
           OR LOWER(dg.nombre_genero) LIKE LOWER(?)
        ORDER BY dt.popularity DESC NULLS LAST, dt.nombre_track
        LIMIT ?
    """, [pattern, pattern, pattern, limit]).fetchall()
    cols = [
        "id_track", "spotify_track_id", "nombre_track",
        "id_artista", "id_album", "id_genero",
        "explicit", "duration_ms", "popularity",
        "nombre_artista", "nombre_genero",
    ]
    return [dict(zip(cols, row)) for row in rows]


def get_track_detail(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    """Full track row with artist, genre, and audio features."""
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
    cols = [
        "id_track", "spotify_track_id", "nombre_track",
        "id_artista", "id_album", "id_genero",
        "explicit", "duration_ms",
        "popularity", "danceability", "energy", "loudness",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo",
        "nombre_artista", "nombre_genero",
    ]
    return dict(zip(cols, rows[0]))