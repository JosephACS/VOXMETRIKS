from __future__ import annotations

import duckdb

from app.core.db import fetch_all
from app.core.exceptions import QueryError
from app.utils.service_result import service_result


def get_pipeline_health(conn: duckdb.DuckDBPyConnection) -> dict:
    stages = fetch_all(
        conn,
        """
        SELECT
            id_stage,
            run_id,
            stage,
            layer,
            started_at,
            duration_ms,
            rows_in,
            rows_out,
            status,
            details
        FROM ctl_pipeline_stages
        ORDER BY started_at DESC
        """
    )
    loads = fetch_all(
        conn,
        """
        SELECT
            id_carga,
            fecha_carga,
            modo,
            registros_nuevos,
            total_raw,
            estado
        FROM ctl_carga_dataset
        ORDER BY fecha_carga DESC
        """
    )
    aggregates = fetch_all(
        conn,
        """
        SELECT
            stage,
            status,
            COUNT(*) AS runs,
            ROUND(AVG(duration_ms), 0) AS avg_duration_ms,
            MAX(duration_ms) AS max_duration_ms,
            SUM(rows_in) AS total_rows_in,
            SUM(rows_out) AS total_rows_out
        FROM ctl_pipeline_stages
        GROUP BY stage, status
        ORDER BY avg_duration_ms DESC
        """
    )

    failed = [
        s for s in stages
        if str(s.get("status", "")).upper() not in {"OK", "EXITOSO"}
    ]
    run_ids = {s["run_id"] for s in stages}
    bottleneck = aggregates[0] if aggregates else None
    last_load = loads[0] if loads else None

    healthy = len(failed) == 0 and len(stages) > 0
    insight = (
        f"Pipeline {'healthy' if healthy else 'degraded'}: {len(run_ids)} runs, "
        f"{len(stages)} stages logged, {len(failed)} failures. "
        f"Bottleneck: {bottleneck['stage']} (~{int(bottleneck['avg_duration_ms'] or 0):,}ms avg)."
        if bottleneck
        else "No pipeline execution history found."
    )
    return service_result(
        insight,
        {"stages": stages, "loads": loads, "stage_aggregates": aggregates},
        {
            "healthy": healthy,
            "total_runs": len(run_ids),
            "total_stages": len(stages),
            "failed_stages": len(failed),
            "last_load_mode": last_load["modo"] if last_load else None,
            "last_load_at": str(last_load["fecha_carga"]) if last_load else None,
            "bottleneck_stage": bottleneck["stage"] if bottleneck else None,
            "bottleneck_avg_ms": int(bottleneck["avg_duration_ms"] or 0) if bottleneck else 0,
        },
    )


def get_data_quality(conn: duckdb.DuckDBPyConnection) -> dict:
    checks: list[dict] = []

    def add(name: str, status: str, detail: str, value=None) -> None:
        checks.append({"check_name": name, "status": status, "detail": detail, "value": value})

    try:
        null_streaming = conn.execute(
            """
            SELECT
                SUM(CASE WHEN id_track IS NULL THEN 1 ELSE 0 END) +
                SUM(CASE WHEN id_usuario IS NULL THEN 1 ELSE 0 END) +
                SUM(CASE WHEN fecha_evento IS NULL THEN 1 ELSE 0 END)
            FROM fact_streaming
            """
        ).fetchone()[0]
        add(
            "fact_streaming_null_keys",
            "pass" if null_streaming == 0 else "fail",
            "Nulls in id_track, id_usuario or fecha_evento",
            int(null_streaming or 0),
        )

        orphan_tracks = conn.execute(
            """
            SELECT COUNT(*)
            FROM fact_streaming f
            LEFT JOIN dim_track t ON t.id_track = f.id_track
            WHERE t.id_track IS NULL
            """
        ).fetchone()[0]
        add(
            "fact_streaming_orphan_tracks",
            "pass" if orphan_tracks == 0 else "fail",
            "Streaming events referencing unknown tracks",
            int(orphan_tracks or 0),
        )

        dup_streaming = conn.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT id_streaming) FROM fact_streaming"
        ).fetchone()[0]
        add(
            "fact_streaming_duplicate_pk",
            "pass" if dup_streaming == 0 else "fail",
            "Duplicate id_streaming values",
            int(dup_streaming or 0),
        )

        agg_sum = conn.execute(
            "SELECT COALESCE(SUM(total_streams), 0) FROM agg_daily_streams"
        ).fetchone()[0]
        fact_count = conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0]
        reconciled = int(agg_sum) == int(fact_count)
        add(
            "agg_daily_vs_fact_events",
            "pass" if reconciled else "warn",
            "SUM(agg_daily_streams.total_streams) vs COUNT(fact_streaming)",
            {"agg_sum": int(agg_sum), "fact_events": int(fact_count)},
        )

        agg_user_plays = conn.execute(
            "SELECT COALESCE(SUM(total_plays), 0) FROM agg_user_activity"
        ).fetchone()[0]
        add(
            "agg_user_vs_fact_streaming",
            "pass" if int(agg_user_plays) == int(fact_count) else "warn",
            "SUM(agg_user_activity.total_plays) vs COUNT(fact_streaming)",
            {"agg_user_plays": int(agg_user_plays), "fact_events": int(fact_count)},
        )

        dim_tracks = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
        agg_pop = conn.execute("SELECT COUNT(*) FROM agg_tracks_populares").fetchone()[0]
        add(
            "dim_track_vs_agg_popularity",
            "pass" if dim_tracks == agg_pop else "fail",
            "dim_track row count vs agg_tracks_populares",
            {"dim_track": int(dim_tracks), "agg_tracks_populares": int(agg_pop)},
        )

        scored = conn.execute("SELECT COUNT(*) FROM agg_recommendation_scores").fetchone()[0]
        coverage = round(100.0 * scored / dim_tracks, 2) if dim_tracks else 0
        add(
            "recommendation_catalog_coverage",
            "warn" if coverage < 10 else "pass",
            "Percentage of catalog with recommendation scores",
            coverage,
        )

        power = conn.execute(
            "SELECT COALESCE(SUM(user_count), 0) FROM agg_user_engagement WHERE segment != 'casual'"
        ).fetchone()[0]
        if power == 0:
            add(
                "user_engagement_segmentation",
                "warn",
                "All users in casual segment — engagement thresholds may be miscalibrated",
                {"non_casual_users": int(power)},
            )

    except Exception as exc:
        raise QueryError(f"Data quality audit failed: {exc}") from exc

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    warnings = sum(1 for c in checks if c["status"] == "warn")
    healthy = failed == 0

    insight = (
        f"Data quality {'passed' if healthy else 'issues detected'}: "
        f"{passed} pass, {warnings} warn, {failed} fail across {len(checks)} checks."
    )
    return service_result(
        insight,
        checks,
        {
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "total_checks": len(checks),
            "healthy": healthy,
        },
    )


# Backward-compatible aliases
get_pipeline_audit = get_pipeline_health
get_data_quality_audit = get_data_quality
