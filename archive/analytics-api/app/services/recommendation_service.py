from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.utils.service_result import service_result


def get_top_recommendations(conn: duckdb.DuckDBPyConnection, limit: int = 50) -> dict:
    rows = fetch_all(
        conn,
        """
        WITH bounds AS (
            SELECT
                quantile_cont(popularity, 0.75) AS p75_pop,
                quantile_cont(popularity, 0.25) AS p25_pop,
                quantile_cont(recommendation_score, 0.75) AS p75_rec,
                quantile_cont(recommendation_score, 0.25) AS p25_rec,
                quantile_cont(engagement_score, 0.75) AS p75_eng,
                quantile_cont(engagement_score, 0.25) AS p25_eng
            FROM agg_recommendation_scores
        ),
        classified AS (
            SELECT
                r.id_track,
                r.nombre_track,
                r.recommendation_score,
                r.engagement_score,
                r.popularity,
                CASE
                    WHEN r.popularity >= b.p75_pop
                         AND r.recommendation_score >= b.p75_rec THEN 'hits'
                    WHEN r.popularity <= b.p25_pop
                         AND (r.recommendation_score >= b.p75_rec
                              OR r.engagement_score >= b.p75_eng) THEN 'hidden_gems'
                    WHEN r.popularity >= b.p75_pop
                         AND r.engagement_score <= b.p25_eng THEN 'overhyped'
                    ELSE 'low_performance'
                END AS segment
            FROM agg_recommendation_scores r
            CROSS JOIN bounds b
        )
        SELECT *
        FROM classified
        ORDER BY recommendation_score DESC, engagement_score DESC
        LIMIT ?
        """,
        [limit],
    )

    segment_counts = fetch_all(
        conn,
        """
        WITH bounds AS (
            SELECT
                quantile_cont(popularity, 0.75) AS p75_pop,
                quantile_cont(popularity, 0.25) AS p25_pop,
                quantile_cont(recommendation_score, 0.75) AS p75_rec,
                quantile_cont(recommendation_score, 0.25) AS p25_rec,
                quantile_cont(engagement_score, 0.75) AS p75_eng,
                quantile_cont(engagement_score, 0.25) AS p25_eng
            FROM agg_recommendation_scores
        ),
        classified AS (
            SELECT
                CASE
                    WHEN r.popularity >= b.p75_pop
                         AND r.recommendation_score >= b.p75_rec THEN 'hits'
                    WHEN r.popularity <= b.p25_pop
                         AND (r.recommendation_score >= b.p75_rec
                              OR r.engagement_score >= b.p75_eng) THEN 'hidden_gems'
                    WHEN r.popularity >= b.p75_pop
                         AND r.engagement_score <= b.p25_eng THEN 'overhyped'
                    ELSE 'low_performance'
                END AS segment
            FROM agg_recommendation_scores r
            CROSS JOIN bounds b
        )
        SELECT segment, COUNT(*) AS track_count
        FROM classified
        GROUP BY segment
        ORDER BY track_count DESC
        """
    )

    scored = conn.execute("SELECT COUNT(*) FROM agg_recommendation_scores").fetchone()[0]
    catalog = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    coverage = round(100.0 * scored / catalog, 2) if catalog else 0.0

    segments_map = {s["segment"]: int(s["track_count"]) for s in segment_counts}
    top_segment = segment_counts[0]["segment"] if segment_counts else "unknown"
    insight = (
        f"Recommendation pool covers {coverage}% of catalog ({scored}/{catalog} tracks). "
        f"Largest segment: {top_segment.replace('_', ' ')} "
        f"({segments_map.get(top_segment, 0)} tracks)."
    )

    return service_result(
        insight,
        rows,
        {
            "returned": len(rows),
            "catalog_size": int(catalog),
            "scored_tracks": int(scored),
            "catalog_coverage_pct": coverage,
            "segments": segments_map,
        },
    )


# Backward-compatible alias
get_recommended_tracks = get_top_recommendations
