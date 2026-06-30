"""Warehouse pipeline status and layer KPIs."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import duckdb

from app.core.query_helpers import count_rows, fetch_rows
from app.core.response_cache import cached_response

from ..paths import BRONZE_PARQUET, GOLD_DIR, PROJECT_ROOT, SILVER_PARQUET
from ..stats.catalog import get_last_loads

logger = logging.getLogger(__name__)


def _file_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else 0.0
    except OSError:
        return 0.0


def _table_counts(conn: duckdb.DuckDBPyConnection, prefix: str) -> Dict[str, int]:
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    out: Dict[str, int] = {}
    for (name,) in tables:
        if name.startswith(prefix):
            out[name] = count_rows(conn, name)
    return out


@cached_response(ttl_seconds=30.0)
def get_warehouse_status(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    db_path = os.environ.get("DB_PATH", str(PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"))
    db_size_mb = _file_mb(Path(db_path))

    dim_counts = _table_counts(conn, "dim_")
    fact_counts = _table_counts(conn, "fact_")
    agg_counts = _table_counts(conn, "agg_")

    stages: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "ctl_pipeline_stages",
            columns=["stage", "layer", "duration_ms", "rows_in", "rows_out", "status", "started_at"],
            order_by="id_stage DESC", limit=8,
        )
        stages = rows
    except Exception:
        logger.exception("get_warehouse_status: ctl_pipeline_stages unavailable")

    loads = []
    try:
        loads = get_last_loads(conn, limit=5)
    except Exception:
        logger.exception("get_warehouse_status: get_last_loads failed")

    last_load = loads[0] if loads else None
    pipeline_status = "healthy" if count_rows(conn, "fact_streaming") >= 100_000 else "degraded"

    return {
        "pipeline_status": pipeline_status,
        "db_size_mb": db_size_mb,
        "layers": {
            "bronze": {"file": str(BRONZE_PARQUET.name), "size_mb": _file_mb(BRONZE_PARQUET)},
            "silver": {"file": str(SILVER_PARQUET.name), "size_mb": _file_mb(SILVER_PARQUET)},
            "gold": {
                "parquet_dir": str(GOLD_DIR),
                "parquet_files": len(list(GOLD_DIR.glob("*.parquet"))) if GOLD_DIR.exists() else 0,
                "dimensions": dim_counts,
                "facts": fact_counts,
                "aggregates": agg_counts,
                "total_rows": sum(dim_counts.values()) + sum(fact_counts.values()) + sum(agg_counts.values()),
            },
        },
        "kpis": {
            "total_tracks": count_rows(conn, "dim_track"),
            "total_streams": count_rows(conn, "fact_streaming"),
            "active_users": count_rows(conn, "dim_usuario"),
            "total_playlists": count_rows(conn, "dim_playlist"),
            "fact_tables_rows": sum(fact_counts.values()),
        },
        "last_load": last_load,
        "recent_stages": stages,
    }
