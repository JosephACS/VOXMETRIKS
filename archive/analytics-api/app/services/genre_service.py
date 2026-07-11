from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.utils.service_result import service_result


def get_genre_trends(conn: duckdb.DuckDBPyConnection, limit: int = 50) -> dict:
    rows = fetch_all(
        conn,
        """
        SELECT
            id_genero,
            nombre_genero,
            streams_7d,
            streams_prev_7d,
            trend_pct,
            avg_popularity
        FROM agg_genre_trends
        ORDER BY trend_pct DESC, streams_7d DESC
        LIMIT ?
        """,
        [limit],
    )
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_genres,
            ROUND(MAX(trend_pct), 2) AS max_trend_pct,
            SUM(CASE WHEN trend_pct > 0 THEN 1 ELSE 0 END) AS rising_genres,
            SUM(CASE WHEN trend_pct < 0 THEN 1 ELSE 0 END) AS declining_genres
        FROM agg_genre_trends
        """
    ).fetchone()

    top = rows[0] if rows else None
    insight = (
        f"Fastest rising genre: {top['nombre_genero']} ({top['trend_pct']:+.1f}% WoW, "
        f"{top['streams_7d']} streams in 7d)."
        if top
        else "No genre trend data available."
    )
    return service_result(
        insight,
        rows,
        {
            "returned": len(rows),
            "total_genres": int(stats[0] or 0),
            "max_trend_pct": float(stats[1] or 0),
            "rising_genres": int(stats[2] or 0),
            "declining_genres": int(stats[3] or 0),
        },
    )


def get_genre_popularity(conn: duckdb.DuckDBPyConnection, limit: int = 50) -> dict:
    rows = fetch_all(
        conn,
        """
        SELECT
            p.id_genero,
            p.nombre_genero,
            p.popularidad_promedio,
            p.energia_promedio,
            p.total_tracks,
            p.total_artistas,
            COALESCE(t.trend_pct, 0) AS trend_pct,
            ROUND(COALESCE(t.trend_pct, 0) * COALESCE(p.popularidad_promedio, 0), 2) AS momentum_score
        FROM agg_genero_popularidad p
        LEFT JOIN agg_genre_trends t ON t.id_genero = p.id_genero
        ORDER BY momentum_score DESC, p.popularidad_promedio DESC
        LIMIT ?
        """,
        [limit],
    )
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_genres,
            ROUND(AVG(popularidad_promedio), 2) AS avg_popularity,
            ROUND(MAX(
                COALESCE(t.trend_pct, 0) * COALESCE(p.popularidad_promedio, 0)
            ), 2) AS max_momentum_score
        FROM agg_genero_popularidad p
        LEFT JOIN agg_genre_trends t ON t.id_genero = p.id_genero
        """
    ).fetchone()

    leader = rows[0] if rows else None
    insight = (
        f"Highest momentum: {leader['nombre_genero']} "
        f"(score {leader['momentum_score']}, trend {leader['trend_pct']:+.1f}%, "
        f"popularity {leader['popularidad_promedio']})."
        if leader
        else "No genre popularity data available."
    )
    return service_result(
        insight,
        rows,
        {
            "returned": len(rows),
            "total_genres": int(stats[0] or 0),
            "avg_popularity": float(stats[1] or 0),
            "max_momentum_score": float(stats[2] or 0),
        },
    )
