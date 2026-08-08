"""Track catalog mutations (create, update, delete)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import duckdb

from .detail import get_track_by_id_raw


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
    title = nombre_track.strip()
    dup = conn.execute(
        """
        SELECT id_track FROM dim_track
        WHERE LOWER(TRIM(nombre_track)) = LOWER(?)
        LIMIT 1
        """,
        [title],
    ).fetchone()
    if dup:
        return {"duplicate": True, "id_track": int(dup[0]), "nombre_track": title}
    if spotify_track_id:
        sid = spotify_track_id.strip()
        dup_sid = conn.execute(
            "SELECT id_track FROM dim_track WHERE spotify_track_id = ? LIMIT 1",
            [sid],
        ).fetchone()
        if dup_sid:
            return {
                "duplicate": True,
                "id_track": int(dup_sid[0]),
                "spotify_track_id": sid,
                "nombre_track": title,
            }
    row = conn.execute("SELECT COALESCE(MAX(id_track), 0) + 1 FROM dim_track").fetchone()
    new_id = row[0]
    conn.execute(
        """INSERT INTO dim_track
           (id_track, spotify_track_id, nombre_track, id_artista, id_album,
            id_genero, explicit, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [new_id, spotify_track_id, title,
         id_artista, id_album, id_genero, explicit, duration_ms]
    )
    return {
        "id_track": new_id,
        "spotify_track_id": spotify_track_id,
        "nombre_track": title,
        "id_artista": id_artista,
        "id_album": id_album,
        "id_genero": id_genero,
        "explicit": explicit,
        "duration_ms": duration_ms,
        "duplicate": False,
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
    existing = get_track_by_id_raw(conn, track_id)
    if not existing:
        return None

    updates = []
    params = []

    if nombre_track is not None:
        title = nombre_track.strip()
        dup = conn.execute(
            """
            SELECT id_track FROM dim_track
            WHERE LOWER(TRIM(nombre_track)) = LOWER(?)
              AND id_track != ?
            LIMIT 1
            """,
            [title, track_id],
        ).fetchone()
        if dup:
            return {"duplicate": True, "id_track": int(dup[0]), "nombre_track": title}
        updates.append("nombre_track = ?")
        params.append(title)
    if spotify_track_id is not None:
        sid = spotify_track_id.strip() if spotify_track_id else spotify_track_id
        if sid:
            dup_sid = conn.execute(
                """
                SELECT id_track FROM dim_track
                WHERE spotify_track_id = ? AND id_track != ?
                LIMIT 1
                """,
                [sid, track_id],
            ).fetchone()
            if dup_sid:
                return {"duplicate": True, "id_track": int(dup_sid[0]), "spotify_track_id": sid}
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
    return get_track_by_id_raw(conn, track_id)


def delete_track(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> bool:
    existing = get_track_by_id_raw(conn, track_id)
    if not existing:
        return False
    conn.execute("DELETE FROM dim_track WHERE id_track = ?", [track_id])
    return True
