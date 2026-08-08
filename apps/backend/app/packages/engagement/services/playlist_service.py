"""Playlist CRUD — app_playlist + app_playlist_track, tracks from dim_track."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb

from app.core.time_util import utc_now

from app.packages.catalog.services.display_text import clean_catalog_row
from app.packages.catalog.services.tracks.playback_availability import (
    playback_status_for_cache,
)
from app.packages.streaming.services.audio.cache import read_cache

from .app_storage import ensure_app_tables


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _track_exists(conn: duckdb.DuckDBPyConnection, track_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM dim_track WHERE id_track = ?", [track_id]
    ).fetchone()
    return row is not None


def _enrich_tracks(conn: duckdb.DuckDBPyConnection, track_ids: List[int]) -> List[Dict[str, Any]]:
    if not track_ids:
        return []
    placeholders = ", ".join(["?"] * len(track_ids))
    rows = conn.execute(f"""
        SELECT
            dt.id_track, dt.nombre_track, dt.id_artista, dt.id_genero,
            dt.duration_ms, dt.popularity,
            da.nombre_artista, dg.nombre_genero
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE dt.id_track IN ({placeholders})
    """, track_ids).fetchall()
    cols = [
        "id_track", "nombre_track", "id_artista", "id_genero",
        "duration_ms", "popularity", "nombre_artista", "nombre_genero",
    ]
    by_id = {r[0]: clean_catalog_row(dict(zip(cols, r))) for r in rows}
    ordered = [by_id[tid] for tid in track_ids if tid in by_id]
    for item in ordered:
        cached = read_cache(conn, int(item["id_track"]))
        item["playback_status"] = playback_status_for_cache(cached)
        item["source_unavailable"] = item["playback_status"] != "playable"
    return ordered


def list_playlists(conn: duckdb.DuckDBPyConnection, user_id: int) -> List[Dict[str, Any]]:
    ensure_app_tables(conn)
    rows = conn.execute("""
        SELECT
            p.id, p.name, p.description, p.created_at,
            COUNT(pt.track_id) AS total_tracks
        FROM app_playlist p
        LEFT JOIN app_playlist_track pt ON pt.playlist_id = p.id
        WHERE p.user_id = ?
        GROUP BY p.id, p.name, p.description, p.created_at
        ORDER BY p.created_at DESC
    """, [user_id]).fetchall()
    result = []
    for r in rows:
        pid = int(r[0])
        preview_rows = conn.execute(
            """
            SELECT track_id
            FROM app_playlist_track
            WHERE playlist_id = ?
            ORDER BY added_at DESC
            LIMIT 4
            """,
            [pid],
        ).fetchall()
        preview_ids = [int(x[0]) for x in preview_rows]
        result.append({
            "id": pid,
            "name": r[1],
            "description": r[2],
            "created_at": str(r[3]) if r[3] else None,
            "total_tracks": int(r[4] or 0),
            "cover_track_id": preview_ids[0] if preview_ids else None,
            "preview_track_ids": preview_ids,
        })
    return result


def get_playlist(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, user_id: int
) -> Optional[Dict[str, Any]]:
    ensure_app_tables(conn)
    row = conn.execute(
        "SELECT id, name, description, created_at FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    ).fetchone()
    if not row:
        return None
    track_rows = conn.execute(
        "SELECT track_id FROM app_playlist_track WHERE playlist_id = ? ORDER BY added_at DESC",
        [playlist_id],
    ).fetchall()
    track_ids = [r[0] for r in track_rows]
    tracks = _enrich_tracks(conn, track_ids)
    preview_ids = [int(t) for t in track_ids[:4]]
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": str(row[3]) if row[3] else None,
        "total_tracks": len(tracks),
        "cover_track_id": preview_ids[0] if preview_ids else None,
        "preview_track_ids": preview_ids,
        "tracks": tracks,
    }


def create_playlist(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    name: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_app_tables(conn)
    from app.packages.personal_subscriptions.application.entitlements import (
        assert_can_create_playlist,
    )
    from app.packages.personal_subscriptions.domain.errors import EntitlementLimitError

    try:
        assert_can_create_playlist(conn, user_id)
    except EntitlementLimitError as exc:
        raise ValueError(str(exc)) from exc
    new_id = _next_id(conn, "app_playlist")
    conn.execute(
        "INSERT INTO app_playlist (id, name, description, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
        [new_id, name.strip(), description, utc_now(), user_id],
    )
    return {
        "id": new_id,
        "name": name.strip(),
        "description": description,
        "created_at": utc_now().isoformat(),
        "total_tracks": 0,
    }


def add_track_to_playlist(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, track_id: int, user_id: int
) -> bool:
    ensure_app_tables(conn)
    exists = conn.execute(
        "SELECT 1 FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    ).fetchone()
    if not exists or not _track_exists(conn, track_id):
        return False
    dup = conn.execute(
        "SELECT 1 FROM app_playlist_track WHERE playlist_id = ? AND track_id = ?",
        [playlist_id, track_id],
    ).fetchone()
    if dup:
        return True
    conn.execute(
        "INSERT INTO app_playlist_track (playlist_id, track_id, added_at) VALUES (?, ?, ?)",
        [playlist_id, track_id, utc_now()],
    )
    return True


def update_playlist(
    conn: duckdb.DuckDBPyConnection,
    playlist_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    ensure_app_tables(conn)
    row = conn.execute(
        "SELECT id, name, description, created_at FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    ).fetchone()
    if not row:
        return None
    new_name = name.strip() if name and name.strip() else row[1]
    new_desc = description if description is not None else row[2]
    conn.execute(
        "UPDATE app_playlist SET name = ?, description = ? WHERE id = ? AND user_id = ?",
        [new_name, new_desc, playlist_id, user_id],
    )
    count = conn.execute(
        "SELECT COUNT(*) FROM app_playlist_track WHERE playlist_id = ?",
        [playlist_id],
    ).fetchone()[0]
    return {
        "id": playlist_id,
        "name": new_name,
        "description": new_desc,
        "created_at": str(row[3]) if row[3] else None,
        "total_tracks": int(count or 0),
    }


def delete_playlist(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, user_id: int
) -> bool:
    ensure_app_tables(conn)
    owned = conn.execute(
        "SELECT 1 FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    ).fetchone()
    if not owned:
        return False
    conn.execute(
        "DELETE FROM app_playlist_track WHERE playlist_id = ?",
        [playlist_id],
    )
    conn.execute(
        "DELETE FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    )
    return True


def remove_track_from_playlist(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, track_id: int, user_id: int
) -> bool:
    ensure_app_tables(conn)
    owned = conn.execute(
        "SELECT 1 FROM app_playlist WHERE id = ? AND user_id = ?",
        [playlist_id, user_id],
    ).fetchone()
    if not owned:
        return False
    conn.execute(
        "DELETE FROM app_playlist_track WHERE playlist_id = ? AND track_id = ?",
        [playlist_id, track_id],
    )
    return True
