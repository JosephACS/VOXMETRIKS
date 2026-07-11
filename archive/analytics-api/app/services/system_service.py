from __future__ import annotations

import time

import duckdb

from app.core.config import get_settings
from app.core.db import fetch_all, fetch_scalar, measure_latency
from app.services import audit_service
from app.utils.service_result import service_result

_LAYER_MAP = {
    "raw_spotify": "raw",
    "dim_": "dimensional",
    "fact_": "fact",
    "agg_": "aggregate",
    "ctl_": "control",
    "app_": "operational",
}

_KEY_TABLES = (
    "fact_streaming",
    "dim_track",
    "dim_usuario",
    "agg_daily_streams",
    "agg_artist_growth",
    "ctl_pipeline_stages",
)


def _resolve_layer(table_name: str) -> str:
    for prefix, layer in _LAYER_MAP.items():
        if table_name.startswith(prefix):
            return layer
    return "other"


def get_full_health(conn: duckdb.DuckDBPyConnection) -> dict:
    settings = get_settings()
    started = time.perf_counter()

    db_path = settings.db_path_resolved
    db_exists = db_path.exists()
    size_mb = round(db_path.stat().st_size / 1024 / 1024, 2) if db_exists else 0.0

    duckdb_version = fetch_scalar(conn, "SELECT version()", label="health_version")
    table_names = [
        r["table_name"]
        for r in fetch_all(
            conn,
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """,
            label="health_tables",
            use_cache=True,
        )
    ]

    latency_probes = [
        {"label": "ping", "latency_ms": measure_latency(conn, "SELECT 1", "health_ping")},
        {
            "label": "fact_streaming_count",
            "latency_ms": measure_latency(conn, "SELECT COUNT(*) FROM fact_streaming", "health_fact_count"),
        },
        {
            "label": "agg_daily_streams_scan",
            "latency_ms": measure_latency(
                conn, "SELECT COALESCE(SUM(total_streams), 0) FROM agg_daily_streams", "health_agg_daily"
            ),
        },
    ]

    estimated = {
        row["table_name"]: row.get("estimated_size")
        for row in fetch_all(
            conn,
            """
            SELECT table_name, estimated_size
            FROM duckdb_tables()
            WHERE schema_name = 'main'
            """,
            label="health_table_sizes",
            use_cache=True,
        )
    }

    counts_sql = " UNION ALL ".join(
        f"SELECT '{table}' AS table_name, COUNT(*) AS row_count FROM {table}"
        for table in _KEY_TABLES
        if table in table_names
    )
    key_counts = (
        fetch_all(conn, counts_sql, label="health_key_counts")
        if counts_sql
        else []
    )
    count_map = {row["table_name"]: int(row["row_count"]) for row in key_counts}

    tables = [
        {
            "table_name": name,
            "row_count": count_map.get(name, 0),
            "estimated_size": estimated.get(name),
            "layer": _resolve_layer(name),
        }
        for name in sorted(table_names)
    ]

    pipeline_payload = audit_service.get_pipeline_health(conn)
    dq_payload = audit_service.get_data_quality(conn)
    pipeline_metrics = pipeline_payload["metrics"]
    dq_metrics = dq_payload["metrics"]

    db_ok = db_exists and duckdb_version is not None
    pipeline_ok = bool(pipeline_metrics.get("healthy"))
    dq_ok = bool(dq_metrics.get("healthy"))
    overall_ok = db_ok and pipeline_ok and dq_ok

    total_latency_ms = round((time.perf_counter() - started) * 1000, 2)

    insight = (
        f"System {'healthy' if overall_ok else 'degraded'} in {settings.environment} — "
        f"DB {size_mb}MB, {len(table_names)} tables, "
        f"pipeline {'OK' if pipeline_ok else 'issues'}, "
        f"DQ {dq_metrics.get('passed', 0)} pass / {dq_metrics.get('failed', 0)} fail, "
        f"probe {total_latency_ms}ms."
    )

    return service_result(
        insight,
        {
            "status": "ok" if overall_ok else "degraded",
            "environment": settings.environment,
            "database": {
                "status": "ok" if db_ok else "unavailable",
                "path": str(db_path),
                "size_mb": size_mb,
                "duckdb_version": duckdb_version,
                "table_count": len(table_names),
            },
            "pipeline": {
                "healthy": pipeline_ok,
                "total_runs": pipeline_metrics.get("total_runs", 0),
                "failed_stages": pipeline_metrics.get("failed_stages", 0),
                "last_stage": pipeline_metrics.get("bottleneck_stage"),
                "last_status": "OK" if pipeline_ok else "degraded",
                "bottleneck_stage": pipeline_metrics.get("bottleneck_stage"),
            },
            "data_quality": {
                "healthy": dq_ok,
                "passed": dq_metrics.get("passed", 0),
                "warnings": dq_metrics.get("warnings", 0),
                "failed": dq_metrics.get("failed", 0),
            },
            "query_latency": latency_probes,
            "tables": tables if settings.health_verbose else tables[:25],
            "total_latency_ms": total_latency_ms,
        },
        {
            "overall_healthy": overall_ok,
            "cache_enabled": settings.cache_enabled,
            "tables_sampled": len(tables) if settings.health_verbose else min(len(tables), 25),
            "key_table_counts": count_map,
            "avg_probe_latency_ms": round(
                sum(p["latency_ms"] for p in latency_probes) / len(latency_probes), 2
            ),
        },
    )
