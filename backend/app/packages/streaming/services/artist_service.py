"""backend/services/artist_service.py"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows

# Expande colaboraciones "Artista A;Artista B" en artistas individuales
_SPLIT_EXPR = "TRIM(unnest(string_split(REPLACE(nombre_artista, ',', ';'), ';')))"

_INDIVIDUALS_CTE = f"""
WITH split AS (
  SELECT id_artista, {_SPLIT_EXPR} AS nombre_artista
  FROM dim_artista
  WHERE nombre_artista IS NOT NULL AND nombre_artista != ''
),
individuals AS (
  SELECT MIN(id_artista) AS id_artista, nombre_artista
  FROM split
  WHERE nombre_artista != ''
  GROUP BY nombre_artista
)
"""


def _query_individuals(
    conn: duckdb.DuckDBPyConnection,
    search: Optional[str],
    limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    where = "WHERE LOWER(nombre_artista) LIKE LOWER(?)" if search else ""
    params: List[Any] = [f"%{search}%"] if search else []
    sql = f"""
    {_INDIVIDUALS_CTE}
    SELECT id_artista, nombre_artista FROM individuals
    {where}
    ORDER BY nombre_artista
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [{"id_artista": r[0], "nombre_artista": r[1]} for r in rows]


def _count_individuals(
    conn: duckdb.DuckDBPyConnection,
    search: Optional[str],
) -> int:
    where = "WHERE LOWER(nombre_artista) LIKE LOWER(?)" if search else ""
    params: List[Any] = [f"%{search}%"] if search else []
    sql = f"{_INDIVIDUALS_CTE} SELECT COUNT(*) FROM individuals {where}"
    row = conn.execute(sql, params).fetchone()
    return int(row[0] if row else 0)


def get_artists(
    conn: duckdb.DuckDBPyConnection,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * limit
    rows = _query_individuals(conn, search, limit, offset)
    total = _count_individuals(conn, search)
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
    row = conn.execute(
        "SELECT nombre_artista FROM dim_artista WHERE id_artista = ?",
        [artist_id],
    ).fetchone()
    if not row:
        return None
    name = row[0]
    primary = name.split(";")[0].strip()
    sql = """
    WITH track_artists AS (
      SELECT dt.popularity,
             TRIM(unnest(string_split(REPLACE(da.nombre_artista, ',', ';'), ';'))) AS nombre_artista
      FROM dim_track dt
      JOIN dim_artista da ON da.id_artista = dt.id_artista
      WHERE da.nombre_artista IS NOT NULL
    )
    SELECT nombre_artista,
           ROUND(AVG(popularity), 1) AS promedio_popularidad,
           COUNT(*) AS total_tracks
    FROM track_artists
    WHERE LOWER(nombre_artista) = LOWER(?)
    GROUP BY nombre_artista
    """
    result = conn.execute(sql, [primary]).fetchone()
    if not result:
        rows, _ = fetch_rows(
            conn, "agg_top_artistas",
            columns=["id_artista", "nombre_artista", "promedio_popularidad", "total_tracks"],
            where="id_artista = ?",
            params=[artist_id],
        )
        return rows[0] if rows else None
    return {
        "id_artista": artist_id,
        "nombre_artista": result[0],
        "promedio_popularidad": float(result[1] or 0),
        "total_tracks": int(result[2] or 0),
    }


def get_top_artists(
    conn: duckdb.DuckDBPyConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    sql = f"""
    WITH track_artists AS (
      SELECT dt.popularity,
             TRIM(unnest(string_split(REPLACE(da.nombre_artista, ',', ';'), ';'))) AS nombre_artista
      FROM dim_track dt
      JOIN dim_artista da ON da.id_artista = dt.id_artista
      WHERE da.nombre_artista IS NOT NULL
    )
    SELECT nombre_artista,
           ROUND(AVG(popularity), 1) AS promedio_popularidad,
           COUNT(*) AS total_tracks
    FROM track_artists
    WHERE nombre_artista != ''
    GROUP BY nombre_artista
    ORDER BY promedio_popularidad DESC
    LIMIT ?
    """
    try:
        rows = conn.execute(sql, [limit]).fetchall()
        return [
            {
                "id_artista": i + 1,
                "nombre_artista": r[0],
                "promedio_popularidad": float(r[1] or 0),
                "total_tracks": int(r[2] or 0),
            }
            for i, r in enumerate(rows)
        ]
    except Exception:
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
