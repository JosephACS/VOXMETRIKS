from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.utils.service_result import service_result

_GROWTH_TOP_N = 20
_EMERGING_LIMIT = 20


def get_artist_growth(conn: duckdb.DuckDBPyConnection) -> dict:
    rows = fetch_all(
        conn,
        """
        SELECT
            id_artista,
            nombre_artista,
            streams_7d,
            streams_30d,
            growth_pct,
            total_followers
        FROM agg_artist_growth
        WHERE streams_7d > 0 OR streams_30d > 0
        ORDER BY growth_pct DESC, streams_7d DESC
        LIMIT ?
        """,
        [_GROWTH_TOP_N],
        label="artist_growth_top",
        use_cache=True,
    )
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS catalog_size,
            ROUND(MAX(growth_pct), 2) AS max_growth_pct,
            ROUND(AVG(growth_pct), 2) AS avg_growth_pct,
            SUM(streams_7d) AS total_streams_7d
        FROM agg_artist_growth
        WHERE streams_7d > 0 OR streams_30d > 0
        """
    ).fetchone()

    top = rows[0] if rows else None
    insight = (
        f"Top growth artist: {top['nombre_artista']} (+{top['growth_pct']}% "
        f"with {top['streams_7d']} streams in 7d)."
        if top
        else "No artist growth data available."
    )
    return service_result(
        insight,
        rows,
        {
            "top_n": _GROWTH_TOP_N,
            "returned": len(rows),
            "catalog_size": int(stats[0] or 0),
            "max_growth_pct": float(stats[1] or 0),
            "avg_growth_pct": float(stats[2] or 0),
            "total_streams_7d": int(stats[3] or 0),
        },
    )


def get_top_artists(conn: duckdb.DuckDBPyConnection, limit: int = 50) -> dict:
    rows = fetch_all(
        conn,
        """
        SELECT
            id_artista,
            nombre_artista,
            promedio_popularidad,
            total_tracks,
            total_streams
        FROM agg_top_artistas
        ORDER BY total_streams DESC, promedio_popularidad DESC
        LIMIT ?
        """,
        [limit],
    )
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS catalog_size,
            SUM(total_streams) AS total_streams,
            ROUND(AVG(promedio_popularidad), 2) AS avg_popularity
        FROM agg_top_artistas
        """
    ).fetchone()

    leader = rows[0] if rows else None
    insight = (
        f"Volume leader: {leader['nombre_artista']} with "
        f"{leader['total_streams']:,} total streams across {leader['total_tracks']} tracks."
        if leader
        else "No artist ranking data available."
    )
    return service_result(
        insight,
        rows,
        {
            "returned": len(rows),
            "catalog_size": int(stats[0] or 0),
            "total_streams": int(stats[1] or 0),
            "avg_popularity": float(stats[2] or 0),
        },
    )


def get_emerging_artists(conn: duckdb.DuckDBPyConnection) -> dict:
    rows = fetch_all(
        conn,
        """
        WITH thresholds AS (
            SELECT
                quantile_cont(growth_pct, 0.75) AS min_growth,
                quantile_cont(total_followers, 0.25) AS max_followers
            FROM agg_artist_growth
            WHERE growth_pct > 0
        )
        SELECT
            a.id_artista,
            a.nombre_artista,
            a.streams_7d,
            a.streams_30d,
            a.growth_pct,
            a.total_followers,
            ROUND(a.growth_pct / NULLIF(a.total_followers, 0) * 1000, 4) AS growth_per_1k_followers
        FROM agg_artist_growth a
        CROSS JOIN thresholds t
        WHERE a.growth_pct >= t.min_growth
          AND a.total_followers <= t.max_followers
          AND a.streams_7d > 0
        ORDER BY a.growth_pct DESC, a.total_followers ASC
        LIMIT ?
        """,
        [_EMERGING_LIMIT],
    )
    stats = conn.execute(
        """
        SELECT
            quantile_cont(growth_pct, 0.75) AS p75_growth,
            quantile_cont(total_followers, 0.25) AS p25_followers
        FROM agg_artist_growth
        WHERE growth_pct > 0
        """
    ).fetchone()

    leader = rows[0] if rows else None
    insight = (
        f"Emerging signal: {leader['nombre_artista']} shows {leader['growth_pct']}% growth "
        f"with only {leader['total_followers']:,} followers — high momentum, low saturation."
        if leader
        else "No emerging artists match high-growth + low-follower criteria."
    )
    return service_result(
        insight,
        rows,
        {
            "returned": len(rows),
            "threshold_growth_pct_p75": round(float(stats[0] or 0), 2),
            "threshold_followers_p25": int(stats[1] or 0),
            "limit": _EMERGING_LIMIT,
        },
    )
