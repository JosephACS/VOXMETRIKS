from __future__ import annotations

import time
from typing import Any

import duckdb

from app.core.cache import cache_invalidate
from app.core.logging import get_logger
from app.etl.gold.artist_analytics import build_agg_artist_growth
from app.etl.gold.dashboard_cache import build_agg_dashboard_cache
from app.etl.gold.genre_analytics import build_agg_genero_popularidad, build_agg_genre_trends
from app.etl.gold.metrics_daily import build_agg_daily_streams, build_agg_platform_usage
from app.etl.gold.track_analytics import build_agg_tracks_populares
from app.etl.gold.user_analytics import build_agg_user_engagement

logger = get_logger(__name__)

GOLD_BUILDERS = [
    ("agg_daily_streams", build_agg_daily_streams),
    ("agg_artist_growth", build_agg_artist_growth),
    ("agg_tracks_populares", build_agg_tracks_populares),
    ("agg_genero_popularidad", build_agg_genero_popularidad),
    ("agg_genre_trends", build_agg_genre_trends),
    ("agg_user_engagement", build_agg_user_engagement),
    ("agg_platform_usage", build_agg_platform_usage),
    ("agg_dashboard_cache", build_agg_dashboard_cache),
]


def run_gold_pipeline(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Build all Gold aggregate tables from Silver + warehouse dimensions."""
    logger.info("[GOLD] Pipeline started")
    started = time.perf_counter()
    stages: list[dict[str, Any]] = []
    rows_out: dict[str, int] = {}

    for table_name, builder in GOLD_BUILDERS:
        try:
            count = builder(conn)
            stages.append({"table": table_name, "rows": count, "status": "ok"})
            rows_out[table_name] = count
        except Exception as exc:
            logger.exception("[GOLD] Failed building %s", table_name)
            stages.append({"table": table_name, "rows": 0, "status": "error", "error": str(exc)})
            raise

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    cache_invalidate("dashboard.")
    cache_invalidate("analytics.")
    logger.info("[GOLD] SUCCESS pipeline completed elapsed_ms=%s tables=%s", elapsed_ms, len(stages))
    return {
        "layer": "gold",
        "status": "ok",
        "elapsed_ms": elapsed_ms,
        "stages": stages,
        "rows_out": rows_out,
    }
