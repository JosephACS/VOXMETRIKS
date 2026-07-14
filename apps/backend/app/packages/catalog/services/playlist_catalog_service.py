"""Browse warehouse playlists (dim_playlist) with tracks from fact_playlist_activity."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb

from app.core.database import get_table_columns, table_exists
from app.packages.engagement.services.playlist_service import _enrich_tracks


def _name_col(conn: duckdb.DuckDBPyConnection) -> str:
    cols = {c.lower() for c in get_table_columns(conn, "dim_playlist")}
    if "nombre" in cols:
        return "nombre"
    if "nombre_playlist" in cols:
        return "nombre_playlist"
    raise ValueError("dim_playlist has no name column")


def _has_desc(conn: duckdb.DuckDBPyConnection) -> bool:
    cols = {c.lower() for c in get_table_columns(conn, "dim_playlist")}
    return "descripcion" in cols


def _has_publica(conn: duckdb.DuckDBPyConnection) -> bool:
    cols = {c.lower() for c in get_table_columns(conn, "dim_playlist")}
    return "publica" in cols


def _activity_track_counts_sql() -> str:
    return """
        SELECT id_playlist, COUNT(DISTINCT id_track) AS total_tracks
        FROM fact_playlist_activity
        WHERE action_type IN ('add', 'play')
        GROUP BY id_playlist
    """


def list_catalog_playlists(
    conn: duckdb.DuckDBPyConnection,
    *,
    page: int = 1,
    limit: int = 24,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    if not table_exists(conn, "dim_playlist"):
        return {"total": 0, "page": page, "limit": limit, "items": []}

    name_col = _name_col(conn)
    desc_sql = "dp.descripcion" if _has_desc(conn) else "NULL"
    where = ["1=1"]
    params: list[Any] = []

    if _has_publica(conn):
        where.append("COALESCE(dp.publica, TRUE)")

    term = (search or "").strip()
    if term:
        where.append(f"LOWER(dp.{name_col}) LIKE LOWER(?)")
        params.append(f"%{term}%")

    where_sql = " AND ".join(where)
    has_activity = table_exists(conn, "fact_playlist_activity")
    has_agg = table_exists(conn, "agg_top_playlists")

    if has_activity:
        join_tracks = f"LEFT JOIN ({_activity_track_counts_sql()}) pa ON pa.id_playlist = dp.id_playlist"
        tracks_expr = "COALESCE(pa.total_tracks, 0)"
    elif has_agg:
        join_tracks = "LEFT JOIN agg_top_playlists agg ON agg.id_playlist = dp.id_playlist"
        tracks_expr = "COALESCE(agg.total_tracks, 0)"
    else:
        join_tracks = ""
        tracks_expr = "0"

    order_expr = tracks_expr if has_activity or has_agg else f"dp.{name_col}"
    total = int(
        conn.execute(
            f"SELECT COUNT(*) FROM dim_playlist dp WHERE {where_sql}",
            params,
        ).fetchone()[0]
    )

    offset = max(0, (page - 1) * limit)
    rows = conn.execute(
        f"""
        SELECT
            dp.id_playlist,
            dp.{name_col} AS name,
            {desc_sql} AS description,
            {tracks_expr} AS total_tracks
        FROM dim_playlist dp
        {join_tracks}
        WHERE {where_sql}
        ORDER BY {order_expr} DESC, dp.id_playlist
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    items: List[Dict[str, Any]] = []
    for r in rows:
        pid = int(r[0])
        preview_ids = _preview_track_ids(conn, pid, limit=4) if has_activity else []
        items.append({
            "id": pid,
            "name": r[1],
            "description": r[2],
            "created_at": None,
            "total_tracks": int(r[3] or 0),
            "cover_track_id": preview_ids[0] if preview_ids else None,
            "preview_track_ids": preview_ids,
            "source": "catalog",
        })

    return {"total": total, "page": page, "limit": limit, "items": items}


def list_popular_catalog_playlists(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """Top warehouse playlists by engagement (agg_top_playlists) for home rails."""
    if not table_exists(conn, "dim_playlist"):
        return []

    limit = max(1, min(int(limit), 24))
    name_col = _name_col(conn)
    desc_sql = "dp.descripcion" if _has_desc(conn) else "NULL"
    pub_sql = "AND COALESCE(dp.publica, TRUE)" if _has_publica(conn) else ""
    has_activity = table_exists(conn, "fact_playlist_activity")

    if table_exists(conn, "agg_top_playlists"):
        rows = conn.execute(
            f"""
            SELECT
                dp.id_playlist,
                dp.{name_col} AS name,
                {desc_sql} AS description,
                COALESCE(agg.total_tracks, 0) AS total_tracks
            FROM agg_top_playlists agg
            JOIN dim_playlist dp ON dp.id_playlist = agg.id_playlist
            WHERE 1=1 {pub_sql}
            ORDER BY agg.total_plays DESC, agg.unique_listeners DESC, agg.id_playlist
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    else:
        return list_catalog_playlists(conn, page=1, limit=limit)["items"]

    items: List[Dict[str, Any]] = []
    for r in rows:
        pid = int(r[0])
        preview_ids = _preview_track_ids(conn, pid, limit=4) if has_activity else []
        items.append({
            "id": pid,
            "name": r[1],
            "description": r[2],
            "created_at": None,
            "total_tracks": int(r[3] or 0),
            "cover_track_id": preview_ids[0] if preview_ids else None,
            "preview_track_ids": preview_ids,
            "source": "catalog",
        })
    return items


def get_catalog_playlist(
    conn: duckdb.DuckDBPyConnection, playlist_id: int
) -> Optional[Dict[str, Any]]:
    if not table_exists(conn, "dim_playlist"):
        return None

    name_col = _name_col(conn)
    desc_sql = "descripcion" if _has_desc(conn) else "NULL"
    where_pub = "AND COALESCE(publica, TRUE)" if _has_publica(conn) else ""

    row = conn.execute(
        f"""
        SELECT id_playlist, {name_col}, {desc_sql}
        FROM dim_playlist
        WHERE id_playlist = ? {where_pub}
        """,
        [playlist_id],
    ).fetchone()
    if not row:
        return None

    track_ids = _playlist_track_ids(conn, playlist_id, limit=100)
    tracks = _enrich_tracks(conn, track_ids)
    preview_ids = track_ids[:4]
    return {
        "id": int(row[0]),
        "name": row[1],
        "description": row[2],
        "created_at": None,
        "total_tracks": len(tracks),
        "cover_track_id": preview_ids[0] if preview_ids else None,
        "preview_track_ids": preview_ids,
        "tracks": tracks,
        "source": "catalog",
    }


def _playlist_track_ids(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, *, limit: int = 100
) -> List[int]:
    if not table_exists(conn, "fact_playlist_activity"):
        return []
    rows = conn.execute(
        """
        SELECT id_track
        FROM fact_playlist_activity
        WHERE id_playlist = ?
          AND action_type IN ('add', 'play')
        GROUP BY id_track
        ORDER BY COUNT(*) DESC, MAX(fecha_evento) DESC
        LIMIT ?
        """,
        [playlist_id, limit],
    ).fetchall()
    return [int(r[0]) for r in rows]


def _preview_track_ids(
    conn: duckdb.DuckDBPyConnection, playlist_id: int, *, limit: int = 4
) -> List[int]:
    return _playlist_track_ids(conn, playlist_id, limit=limit)
