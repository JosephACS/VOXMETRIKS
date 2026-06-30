"""Device and platform usage analytics."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import duckdb

from app.core.query_helpers import count_rows, fetch_rows

logger = logging.getLogger(__name__)


def get_platform_analytics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    devices: List[Dict[str, Any]] = []
    platform: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_streaming_devices",
            columns=["device_type", "stream_count", "unique_users", "share_pct"],
            order_by="stream_count DESC",
        )
        devices = rows
    except Exception:
        logger.exception("get_platform_analytics: agg_streaming_devices unavailable")

    try:
        rows, _ = fetch_rows(
            conn, "agg_platform_usage",
            columns=["platform", "device_type", "session_count", "total_streams", "avg_session_min", "share_pct"],
            order_by="total_streams DESC",
        )
        platform = rows
    except Exception:
        logger.exception("get_platform_analytics: agg_platform_usage unavailable")

    return {
        "devices": devices,
        "platform_usage": platform,
        "active_users": count_rows(conn, "dim_usuario"),
        "sessions": count_rows(conn, "fact_stream_sessions"),
        "total_streams": count_rows(conn, "fact_streaming"),
    }
