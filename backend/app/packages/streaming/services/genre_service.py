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
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * limit
    conditions: List[str] = []
    params: List[Any] = []
    if search:
        conditions.append("LOWER(nombre_genero) LIKE LOWER(?)")
        params.append(f"%{search.strip()}%")
    where = " AND ".join(conditions) if conditions else "1=1"

    total = int(
        conn.execute(
            f"SELECT COUNT(*) FROM agg_genero_popularidad WHERE {where}",
            params,
        ).fetchone()[0]
    )
    rows_raw = conn.execute(
        f"""
        SELECT id_genero, nombre_genero, popularidad_promedio, energia_promedio,
               total_tracks, total_artistas
        FROM agg_genero_popularidad
        WHERE {where}
        ORDER BY popularidad_promedio DESC NULLS LAST, nombre_genero
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    ).fetchall()
    cols = [
        "id_genero", "nombre_genero", "popularidad_promedio", "energia_promedio",
        "total_tracks", "total_artistas",
    ]
    return [dict(zip(cols, row)) for row in rows_raw], total


def create_genre(
    conn: duckdb.DuckDBPyConnection, nombre_genero: str
) -> Dict[str, Any]:
    name = nombre_genero.strip()
    existing = conn.execute(
        """
        SELECT id_genero, nombre_genero FROM dim_genero
        WHERE LOWER(TRIM(nombre_genero)) = LOWER(?)
        LIMIT 1
        """,
        [name],
    ).fetchone()
    if existing:
        return {
            "duplicate": True,
            "id_genero": int(existing[0]),
            "nombre_genero": existing[1],
        }
    row = conn.execute("SELECT COALESCE(MAX(id_genero), 0) + 1 FROM dim_genero").fetchone()
    new_id = row[0]
    conn.execute(
        "INSERT INTO dim_genero (id_genero, nombre_genero) VALUES (?, ?)",
        [new_id, name]
    )
    return {"id_genero": new_id, "nombre_genero": name, "duplicate": False}


def update_genre(
    conn: duckdb.DuckDBPyConnection, genre_id: int, nombre_genero: str
) -> Optional[Dict[str, Any]]:
    existing = get_genre_by_id(conn, genre_id)
    if not existing:
        return None
    conn.execute(
        "UPDATE dim_genero SET nombre_genero = ? WHERE id_genero = ?",
        [nombre_genero.strip(), genre_id]
    )
    return {"id_genero": genre_id, "nombre_genero": nombre_genero.strip()}


def delete_genre(
    conn: duckdb.DuckDBPyConnection, genre_id: int
) -> bool:
    existing = get_genre_by_id(conn, genre_id)
    if not existing:
        return False
    conn.execute("DELETE FROM dim_genero WHERE id_genero = ?", [genre_id])
    return True
