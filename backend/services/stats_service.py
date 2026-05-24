"""backend/services/stats_service.py"""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from .base_service import count_rows, fetch_rows


def get_summary(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """High-level counts across all warehouse tables."""
    return {
        "total_tracks":          count_rows(conn, "dim_track"),
        "total_artistas":        count_rows(conn, "dim_artista"),
        "total_generos":         count_rows(conn, "dim_genero"),
        "total_albums":          count_rows(conn, "dim_album"),
        "total_audio_features":  count_rows(conn, "fact_audio_features"),
    }


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
    Join fact_audio_features with dim_track to return top tracks by popularity.
    Only columns that exist in both tables are used.
    """
    rows = conn.execute(f"""
        SELECT
            dt.id_track,
            dt.nombre_track,
            dt.id_artista,
            dt.id_genero,
            faf.popularity,
            faf.energy,
            faf.danceability,
            faf.valence
        FROM fact_audio_features faf
        INNER JOIN dim_track dt ON dt.id_track = faf.id_track
        WHERE faf.popularity IS NOT NULL
        ORDER BY faf.popularity DESC
        LIMIT {int(limit)}
    """).fetchall()

    cols = ["id_track", "nombre_track", "id_artista", "id_genero",
            "popularity", "energy", "danceability", "valence"]
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
    return rows
