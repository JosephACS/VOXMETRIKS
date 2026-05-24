"""backend/services/stats_service.py"""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from .base_service import count_rows, fetch_rows


def get_summary(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """High-level counts + averages across all warehouse tables."""
    result: Dict[str, Any] = {
        "total_tracks":   count_rows(conn, "dim_track"),
        "total_artistas": count_rows(conn, "dim_artista"),
        "total_generos":  count_rows(conn, "dim_genero"),
        "total_albumes":  count_rows(conn, "dim_album"),
        "total_streams":  count_rows(conn, "fact_streaming"),
    }

    # Averages from dim_track (audio features live there now)
    try:
        row = conn.execute("""
            SELECT
                AVG(popularity)    AS promedio_popularidad,
                AVG(energy)        AS promedio_energy,
                AVG(danceability)  AS promedio_danceability,
                AVG(valence)       AS promedio_valence,
                AVG(tempo)         AS promedio_tempo
            FROM dim_track
            WHERE popularity IS NOT NULL
        """).fetchone()
        if row:
            result["promedio_popularidad"]  = round(float(row[0] or 0), 1)
            result["promedio_energy"]       = round(float(row[1] or 0), 4)
            result["promedio_danceability"] = round(float(row[2] or 0), 4)
            result["promedio_valence"]      = round(float(row[3] or 0), 4)
            result["promedio_tempo"]        = round(float(row[4] or 0), 1)
    except Exception:
        result["promedio_popularidad"]  = 0.0
        result["promedio_energy"]       = 0.0
        result["promedio_danceability"] = 0.0
        result["promedio_valence"]      = 0.0
        result["promedio_tempo"]        = 0.0

    return result


def get_energia_distribution(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_distribucion_energia",
        columns=[
            "rango_energia", "cantidad_tracks",
            "popularidad_promedio", "danceability_promedio",
        ],
        order_by="rango_energia",
    )
    return rows


def get_top_tracks_by_popularity(
    conn: duckdb.DuckDBPyConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Top tracks by popularity using dim_track (audio features are stored there)
    joined with dim_artista for the artist name.
    """
    rows = conn.execute(f"""
        SELECT
            dt.id_track,
            dt.nombre_track,
            COALESCE(da.nombre_artista, '—') AS nombre_artista,
            dt.id_artista,
            dt.id_genero,
            dt.popularity,
            dt.energy,
            dt.danceability,
            dt.valence
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.popularity IS NOT NULL
        ORDER BY dt.popularity DESC
        LIMIT {int(limit)}
    """).fetchall()

    cols = [
        "id_track", "nombre_track", "nombre_artista", "id_artista",
        "id_genero", "popularity", "energy", "danceability", "valence",
    ]
    return [dict(zip(cols, row)) for row in rows]


def get_last_loads(
    conn: duckdb.DuckDBPyConnection, limit: int = 5
) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "ctl_carga_dataset",
        columns=["id_carga", "fecha_carga", "modo", "registros_nuevos", "total_raw", "estado"],
        order_by="id_carga DESC",
        limit=limit,
    )
    result = []
    for r in rows:
        result.append({
            "id_carga":         r.get("id_carga"),
            "fecha_carga":      str(r["fecha_carga"]) if r.get("fecha_carga") else None,
            "modo":             r.get("modo", "—"),
            "registros_nuevos": r.get("registros_nuevos", 0),
            "total_raw":        r.get("total_raw", 0),
            "estado":           r.get("estado", "—"),
        })
    return result