"""Favorites — app_favorite table, tracks from dim_track."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.core.time_util import utc_now

from app.packages.catalog.services.display_text import clean_catalog_rows

from app.packages.catalog.services.tracks.playback_availability import (
    playback_status_for_cache,
)
from app.packages.streaming.services.audio.cache import read_cache

from .app_storage import ensure_app_tables


def _with_playback_status(
    conn: duckdb.DuckDBPyConnection, items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    for item in items:
        tid = int(item.get("id_track") or 0)
        cached = read_cache(conn, tid) if tid else None
        item["playback_status"] = playback_status_for_cache(cached)
        item["source_unavailable"] = item["playback_status"] != "playable"
    return items


def list_favorites(conn: duckdb.DuckDBPyConnection, user_id: int) -> List[Dict[str, Any]]:
    from app.core.database import table_exists

    ensure_app_tables(conn)
    # Empty warehouse (no gold): chrome may still call /favorites — return [].
    if not table_exists(conn, "dim_track"):
        return []
    rows = conn.execute("""
        SELECT
            dt.id_track, dt.nombre_track, dt.id_artista, dt.id_genero,
            dt.duration_ms, dt.popularity,
            da.nombre_artista, dg.nombre_genero,
            f.added_at
        FROM app_favorite f
        JOIN dim_track dt ON dt.id_track = f.track_id
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE f.user_id = ?
        ORDER BY f.added_at DESC
    """, [user_id]).fetchall()
    cols = [
        "id_track", "nombre_track", "id_artista", "id_genero",
        "duration_ms", "popularity", "nombre_artista", "nombre_genero", "added_at",
    ]
    result = []
    for r in rows:
        item = dict(zip(cols, r))
        item["added_at"] = str(item["added_at"]) if item["added_at"] else None
        result.append(item)
    return _with_playback_status(conn, clean_catalog_rows(result))


def add_favorite(conn: duckdb.DuckDBPyConnection, user_id: int, track_id: int) -> bool:
    from app.core.database import table_exists

    ensure_app_tables(conn)
    if not table_exists(conn, "dim_track"):
        return False
    row = conn.execute(
        "SELECT 1 FROM dim_track WHERE id_track = ?", [track_id]
    ).fetchone()
    if not row:
        return False
    dup = conn.execute(
        "SELECT 1 FROM app_favorite WHERE user_id = ? AND track_id = ?",
        [user_id, track_id],
    ).fetchone()
    if dup:
        return True
    from app.packages.personal_subscriptions.application.entitlements import (
        assert_can_add_favorite,
    )
    from app.packages.personal_subscriptions.domain.errors import EntitlementLimitError

    try:
        assert_can_add_favorite(conn, user_id)
    except EntitlementLimitError as exc:
        raise ValueError(str(exc)) from exc
    conn.execute(
        "INSERT INTO app_favorite (user_id, track_id, added_at) VALUES (?, ?, ?)",
        [user_id, track_id, utc_now()],
    )
    return True


def remove_favorite(conn: duckdb.DuckDBPyConnection, user_id: int, track_id: int) -> bool:
    ensure_app_tables(conn)
    conn.execute(
        "DELETE FROM app_favorite WHERE user_id = ? AND track_id = ?",
        [user_id, track_id],
    )
    return True


def is_favorite(conn: duckdb.DuckDBPyConnection, user_id: int, track_id: int) -> bool:
    ensure_app_tables(conn)
    row = conn.execute(
        "SELECT 1 FROM app_favorite WHERE user_id = ? AND track_id = ?",
        [user_id, track_id],
    ).fetchone()
    return row is not None


def favorite_ids(conn: duckdb.DuckDBPyConnection, user_id: int) -> List[int]:
    ensure_app_tables(conn)
    rows = conn.execute(
        "SELECT track_id FROM app_favorite WHERE user_id = ?", [user_id]
    ).fetchall()
    return [r[0] for r in rows]
