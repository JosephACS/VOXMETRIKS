"""backend/services/genre_service.py"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows


def get_genres(
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * limit
    where  = "LOWER(nombre_genero) LIKE LOWER(?)" if search else ""
    params = [f"%{search}%"] if search else []

    rows, _ = fetch_rows(
        conn, "dim_genero",
        columns=["id_genero", "nombre_genero"],
        where=where,
        order_by="nombre_genero",
        limit=limit,
        offset=offset,
        params=params,
    )
    total = count_rows(conn, "dim_genero", where=where, params=params)
    return rows, total


def get_genre_by_id(
    conn: duckdb.DuckDBPyConnection, genre_id: int
) -> Optional[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "dim_genero",
        columns=["id_genero", "nombre_genero"],
        where="id_genero = ?",
        params=[genre_id],
    )
    return rows[0] if rows else None


def get_genre_stats(
    conn: duckdb.DuckDBPyConnection, limit: int = 20
) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_genero_popularidad",
        columns=[
            "id_genero", "nombre_genero",
            "popularidad_promedio", "energia_promedio",
            "total_tracks", "total_artistas",
        ],
        order_by="popularidad_promedio DESC",
        limit=limit,
    )
    return rows
