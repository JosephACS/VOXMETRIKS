"""backend/services/artist_service.py"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows


def get_artists(
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * limit
    where  = "LOWER(nombre_artista) LIKE LOWER(?)" if search else ""
    params = [f"%{search}%"] if search else []

    rows, _ = fetch_rows(
        conn, "dim_artista",
        columns=["id_artista", "nombre_artista"],
        where=where,
        order_by="nombre_artista",
        limit=limit,
        offset=offset,
        params=params,
    )
    total = count_rows(conn, "dim_artista", where=where, params=params)
    return rows, total


def get_artist_by_id(
    conn: duckdb.DuckDBPyConnection, artist_id: int
) -> Optional[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "dim_artista",
        columns=["id_artista", "nombre_artista"],
        where="id_artista = ?",
        params=[artist_id],
    )
    return rows[0] if rows else None


def get_artist_stats(
    conn: duckdb.DuckDBPyConnection, artist_id: int
) -> Optional[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_top_artistas",
        columns=["id_artista", "nombre_artista", "promedio_popularidad", "total_tracks"],
        where="id_artista = ?",
        params=[artist_id],
    )
    return rows[0] if rows else None


def get_top_artists(
    conn: duckdb.DuckDBPyConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_top_artistas",
        columns=["id_artista", "nombre_artista", "promedio_popularidad", "total_tracks"],
        order_by="promedio_popularidad DESC",
        limit=limit,
    )
    return rows


def create_artist(
    conn: duckdb.DuckDBPyConnection, nombre_artista: str
) -> Dict[str, Any]:
    # Get next ID
    row = conn.execute("SELECT COALESCE(MAX(id_artista), 0) + 1 FROM dim_artista").fetchone()
    new_id = row[0]
    conn.execute(
        "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (?, ?)",
        [new_id, nombre_artista.strip()]
    )
    return {"id_artista": new_id, "nombre_artista": nombre_artista.strip()}


def update_artist(
    conn: duckdb.DuckDBPyConnection, artist_id: int, nombre_artista: str
) -> Optional[Dict[str, Any]]:
    existing = get_artist_by_id(conn, artist_id)
    if not existing:
        return None
    conn.execute(
        "UPDATE dim_artista SET nombre_artista = ? WHERE id_artista = ?",
        [nombre_artista.strip(), artist_id]
    )
    return {"id_artista": artist_id, "nombre_artista": nombre_artista.strip()}


def delete_artist(
    conn: duckdb.DuckDBPyConnection, artist_id: int
) -> bool:
    existing = get_artist_by_id(conn, artist_id)
    if not existing:
        return False
    conn.execute("DELETE FROM dim_artista WHERE id_artista = ?", [artist_id])
    return True
