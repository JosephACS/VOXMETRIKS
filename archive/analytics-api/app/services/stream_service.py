from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.utils.service_result import service_result


def get_daily_streams(conn: duckdb.DuckDBPyConnection, days: int = 90) -> dict:
    rows = fetch_all(
        conn,
        """
        SELECT
            fecha,
            total_streams,
            unique_users,
            unique_tracks,
            avg_duration_ms,
            skip_count
        FROM agg_daily_streams
        ORDER BY fecha DESC
        LIMIT ?
        """,
        [days],
    )
    stats = conn.execute(
        """
        SELECT
            COUNT(*) AS days_count,
            COALESCE(SUM(total_streams), 0) AS total_streams,
            ROUND(AVG(unique_users), 1) AS avg_dau,
            ROUND(STDDEV(unique_users), 2) AS dau_stddev,
            ROUND(AVG(total_streams), 1) AS avg_daily_streams
        FROM (
            SELECT total_streams, unique_users
            FROM agg_daily_streams
            ORDER BY fecha DESC
            LIMIT ?
        ) sub
        """,
        [days],
    ).fetchone()

    latest = rows[0] if rows else None
    insight = (
        f"Last {stats[0]} days: {int(stats[1] or 0):,} stream events, "
        f"avg {float(stats[4] or 0):,.0f}/day with DAU ~{float(stats[2] or 0):,.0f}."
        if latest
        else "No daily stream aggregates available."
    )
    return service_result(
        insight,
        rows,
        {
            "days_requested": days,
            "days_returned": int(stats[0] or 0),
            "total_streams": int(stats[1] or 0),
            "avg_dau": float(stats[2] or 0),
            "dau_stddev": float(stats[3] or 0) if stats[3] is not None else 0.0,
            "avg_daily_streams": float(stats[4] or 0),
            "latest_date": str(latest["fecha"]) if latest else None,
        },
    )


def get_engagement_analysis(conn: duckdb.DuckDBPyConnection) -> dict:
    fact = conn.execute(
        """
        SELECT
            COUNT(*) AS total_events,
            SUM(CASE WHEN skipped THEN 1 ELSE 0 END) AS skip_events,
            SUM(CASE WHEN completado THEN 1 ELSE 0 END) AS completed_events,
            ROUND(AVG(COALESCE(duracion_ms, 0)), 0) AS avg_duration_ms
        FROM fact_streaming
        """
    ).fetchone()

    agg = conn.execute(
        """
        SELECT
            COALESCE(SUM(total_streams), 0) AS agg_events,
            COALESCE(SUM(skip_count), 0) AS agg_skips,
            ROUND(AVG(avg_duration_ms), 0) AS agg_avg_duration_ms,
            COUNT(*) AS agg_days
        FROM agg_daily_streams
        """
    ).fetchone()

    total = int(fact[0] or 0)
    skip_events = int(fact[1] or 0)
    completed = int(fact[2] or 0)
    skip_rate = round(100.0 * skip_events / total, 2) if total else 0.0
    completion_rate = round(100.0 * completed / total, 2) if total else 0.0
    avg_duration = float(fact[3] or 0)

    daily_breakdown = fetch_all(
        conn,
        """
        SELECT
            d.fecha,
            d.total_streams,
            d.skip_count,
            ROUND(100.0 * d.skip_count / NULLIF(d.total_streams, 0), 2) AS skip_rate_pct,
            ROUND(100.0 * COALESCE(f.completed, 0) / NULLIF(f.total, 0), 2) AS completion_rate_pct,
            ROUND(COALESCE(d.avg_duration_ms, 0), 0) AS avg_duration_ms
        FROM agg_daily_streams d
        LEFT JOIN (
            SELECT
                CAST(fecha_evento AS DATE) AS fecha,
                COUNT(*) AS total,
                SUM(CASE WHEN completado THEN 1 ELSE 0 END) AS completed
            FROM fact_streaming
            GROUP BY 1
        ) f ON f.fecha = d.fecha
        ORDER BY d.fecha DESC
        LIMIT 30
        """
    )

    agg_reconciled = int(agg[0] or 0) == total
    insight = (
        f"Engagement profile: skip rate {skip_rate}%, completion {completion_rate}%, "
        f"avg listen {avg_duration:,.0f}ms. "
        f"Daily agg reconciles with facts: {'yes' if agg_reconciled else 'no'}."
    )
    return service_result(
        insight,
        daily_breakdown,
        {
            "skip_rate_pct": skip_rate,
            "completion_rate_pct": completion_rate,
            "avg_duration_ms": avg_duration,
            "total_events": total,
            "skip_events": skip_events,
            "completed_events": completed,
            "agg_total_streams": int(agg[0] or 0),
            "agg_skip_count": int(agg[1] or 0),
            "agg_avg_duration_ms": float(agg[2] or 0),
            "agg_days": int(agg[3] or 0),
            "fact_agg_reconciled": agg_reconciled,
        },
    )


# Backward-compatible alias
get_stream_engagement = get_engagement_analysis
