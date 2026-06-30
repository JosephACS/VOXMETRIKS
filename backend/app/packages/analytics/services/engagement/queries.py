"""Engagement, retention, and search analytics."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import duckdb

from app.core.query_helpers import fetch_rows

logger = logging.getLogger(__name__)


def get_engagement_analytics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    skip_rate = 0.0
    completion_rate = 0.0
    avg_session_min = 0.0
    try:
        row = conn.execute("""
            SELECT
                ROUND(SUM(CASE WHEN skipped THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2),
                ROUND(SUM(CASE WHEN completado THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
            FROM fact_streaming
        """).fetchone()
        if row:
            skip_rate = float(row[0] or 0)
            completion_rate = float(row[1] or 0)
    except Exception:
        logger.exception("get_engagement_analytics: skip/completion rates query failed")

    try:
        row = conn.execute("""
            SELECT ROUND(AVG(total_ms) / 60000.0, 2) FROM fact_stream_sessions
        """).fetchone()
        if row and row[0]:
            avg_session_min = float(row[0])
    except Exception:
        logger.exception("get_engagement_analytics: avg session duration query failed")

    segments: List[Dict[str, Any]] = []
    retention: List[Dict[str, Any]] = []
    top_searches: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_user_engagement",
            columns=["segment", "user_count", "avg_plays", "avg_session_min", "retention_pct"],
        )
        segments = rows
    except Exception:
        logger.exception("get_engagement_analytics: agg_user_engagement unavailable")

    try:
        rows, _ = fetch_rows(conn, "agg_user_retention",
                             columns=["cohort_week", "users_cohort", "week_1_pct", "week_2_pct", "week_4_pct"],
                             order_by="cohort_week")
        retention = rows
    except Exception:
        logger.exception("get_engagement_analytics: agg_user_retention unavailable")

    try:
        rows, _ = fetch_rows(conn, "agg_top_searches",
                             columns=["query_text", "search_count", "avg_results"],
                             order_by="search_count DESC", limit=10)
        top_searches = rows
    except Exception:
        logger.exception("get_engagement_analytics: agg_top_searches unavailable")

    engagement_score = 0.0
    try:
        row = conn.execute("SELECT ROUND(AVG(engagement_score), 2) FROM agg_user_activity").fetchone()
        if row and row[0]:
            engagement_score = float(row[0])
    except Exception:
        logger.exception("get_engagement_analytics: agg_user_activity avg unavailable; using derived score")
        engagement_score = round(completion_rate * 0.6 + (100 - skip_rate) * 0.4, 2)

    return {
        "skip_rate": skip_rate,
        "completion_rate": completion_rate,
        "avg_session_time_min": avg_session_min,
        "engagement_score": engagement_score,
        "user_segments": segments,
        "user_retention": retention,
        "top_searches": top_searches,
        "recommendation_avg": engagement_score,
    }
