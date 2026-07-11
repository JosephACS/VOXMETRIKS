from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.utils.service_result import service_result


def get_user_segments(conn: duckdb.DuckDBPyConnection) -> dict:
    segments = fetch_all(
        conn,
        """
        SELECT
            segment,
            user_count,
            avg_plays,
            avg_session_min,
            retention_pct
        FROM agg_user_engagement
        ORDER BY user_count DESC
        """
    )
    total_users = conn.execute("SELECT COUNT(*) FROM dim_usuario").fetchone()[0]
    dominant = segments[0] if segments else None

    high_value = fetch_all(
        conn,
        """
        SELECT id_usuario, total_plays, engagement_score
        FROM agg_user_activity
        WHERE engagement_score >= (
            SELECT quantile_cont(engagement_score, 0.90)
            FROM agg_user_activity
        )
        ORDER BY engagement_score DESC
        LIMIT 10
        """
    )

    insight = (
        f"Dominant segment '{dominant['segment']}': {dominant['user_count']:,} users "
        f"({round(100.0 * dominant['user_count'] / total_users, 1)}% of base), "
        f"avg {dominant['avg_plays']} plays."
        if dominant and total_users
        else "No user segment data available."
    )
    return service_result(
        insight,
        segments,
        {
            "total_users": int(total_users),
            "segment_count": len(segments),
            "high_value_users_sample": len(high_value),
            "high_value_top_score": float(high_value[0]["engagement_score"]) if high_value else 0.0,
        },
    )


def get_retention_analysis(conn: duckdb.DuckDBPyConnection) -> dict:
    cohorts = fetch_all(
        conn,
        """
        SELECT
            cohort_week,
            users_cohort,
            week_1_pct,
            week_2_pct,
            week_4_pct,
            ROUND(week_1_pct - week_4_pct, 2) AS w1_w4_drop_pp
        FROM agg_user_retention
        ORDER BY cohort_week
        """
    )
    stats = conn.execute(
        """
        SELECT
            ROUND(AVG(week_1_pct), 2) AS avg_w1,
            ROUND(AVG(week_4_pct), 2) AS avg_w4,
            ROUND(AVG(week_1_pct - week_4_pct), 2) AS avg_cliff_pp
        FROM agg_user_retention
        """
    ).fetchone()

    churn_risk = [
        c for c in cohorts
        if float(c["week_4_pct"]) < float(stats[1] or 0)
        or float(c["w1_w4_drop_pp"]) > float(stats[2] or 0)
    ]
    high_value = [
        c for c in cohorts
        if float(c["week_1_pct"]) >= float(stats[0] or 0)
        and float(c["week_4_pct"]) >= float(stats[1] or 0)
    ]

    worst = min(cohorts, key=lambda c: float(c["week_4_pct"])) if cohorts else None
    best = max(cohorts, key=lambda c: float(c["week_4_pct"])) if cohorts else None

    insight = (
        f"Retention cliff avg {float(stats[2] or 0):.1f}pp (W1 to W4). "
        f"Churn-risk cohorts: {len(churn_risk)}; high-value cohorts: {len(high_value)}. "
        f"Best W4: {best['cohort_week']} ({best['week_4_pct']}%)."
        if best and worst
        else "No retention cohort data available."
    )
    return service_result(
        insight,
        {
            "cohorts": cohorts,
            "churn_risk": churn_risk,
            "high_value": high_value,
        },
        {
            "total_cohorts": len(cohorts),
            "avg_week_1_pct": float(stats[0] or 0),
            "avg_week_4_pct": float(stats[1] or 0),
            "avg_w1_w4_drop_pp": float(stats[2] or 0),
            "churn_risk_count": len(churn_risk),
            "high_value_count": len(high_value),
            "best_cohort": best["cohort_week"] if best else None,
            "worst_cohort": worst["cohort_week"] if worst else None,
        },
    )


# Backward-compatible alias
get_user_retention = get_retention_analysis
