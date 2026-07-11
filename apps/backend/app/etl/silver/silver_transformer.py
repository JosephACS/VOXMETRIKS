from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.silver.clean_streams import clean_streams
from app.etl.silver.clean_tracks import clean_tracks
from app.etl.silver.clean_users import clean_users

logger = get_logger(__name__)


def run_silver_pipeline(conn: duckdb.DuckDBPyConnection) -> dict:
    """Orchestrate Silver layer: tracks → users → streams."""
    logger.info("[SILVER] Pipeline started")
    stages = [
        clean_tracks(conn),
        clean_users(conn),
        clean_streams(conn),
    ]
    logger.info("[SILVER] Pipeline finished stages=%s", len(stages))
    return {
        "layer": "silver",
        "status": "ok",
        "stages": stages,
        "rows_out": {s["target"]: s["rows_out"] for s in stages},
    }
