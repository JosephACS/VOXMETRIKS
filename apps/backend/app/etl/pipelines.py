from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.etl.bronze.ingest_raw_spotify import ingest_raw_spotify
from app.etl.connection import etl_connection
from app.etl.gold.gold_builder import run_gold_pipeline
from app.etl.silver.silver_transformer import run_silver_pipeline

logger = get_logger(__name__)


def run_bronze_pipeline(
    conn=None,
    *,
    source_table: str = "raw_spotify",
) -> dict[str, Any]:
    """Bronze layer: ingest raw_spotify → bronze_raw_tracks."""
    logger.info("[BRONZE] Pipeline started source=%s", source_table)
    started = time.perf_counter()

    def _execute(connection) -> dict[str, Any]:
        return ingest_raw_spotify(connection, source_table=source_table)

    if conn is not None:
        result = _execute(conn)
    else:
        with etl_connection() as connection:
            result = _execute(connection)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    result["elapsed_ms"] = elapsed_ms
    logger.info("[BRONZE] Pipeline finished elapsed_ms=%s rows_out=%s", elapsed_ms, result.get("rows_out"))
    return result


def run_silver_pipeline_wrapper(conn=None) -> dict[str, Any]:
    """Silver layer wrapper with optional shared connection."""
    logger.info("[SILVER] Pipeline wrapper started")
    started = time.perf_counter()

    if conn is not None:
        result = run_silver_pipeline(conn)
    else:
        with etl_connection() as connection:
            result = run_silver_pipeline(connection)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    result["elapsed_ms"] = elapsed_ms
    logger.info("[SILVER] Pipeline wrapper finished elapsed_ms=%s", elapsed_ms)
    return result


def run_gold_pipeline_wrapper(conn=None) -> dict[str, Any]:
    """Gold layer wrapper with optional shared connection."""
    logger.info("[GOLD] Pipeline wrapper started")
    if conn is not None:
        return run_gold_pipeline(conn)
    with etl_connection() as connection:
        return run_gold_pipeline(connection)


def run_full_etl(*, source_table: str = "raw_spotify") -> dict[str, Any]:
    """Full Medallion ETL: Bronze → Silver → Gold in a single write connection."""
    logger.info("[ETL] Full pipeline started")
    started = time.perf_counter()
    errors: list[str] = []
    bronze: dict[str, Any] = {}
    silver: dict[str, Any] = {}
    gold: dict[str, Any] = {}

    try:
        with etl_connection() as conn:
            try:
                bronze = run_bronze_pipeline(conn, source_table=source_table)
            except Exception as exc:
                logger.exception("[ETL] Bronze pipeline failed")
                errors.append(f"bronze: {exc}")
                bronze = {"status": "error", "error": str(exc)}

            if not errors:
                try:
                    silver = run_silver_pipeline_wrapper(conn)
                except Exception as exc:
                    logger.exception("[ETL] Silver pipeline failed")
                    errors.append(f"silver: {exc}")
                    silver = {"status": "error", "error": str(exc)}

            if not errors:
                try:
                    gold = run_gold_pipeline_wrapper(conn)
                except Exception as exc:
                    logger.exception("[ETL] Gold pipeline failed")
                    errors.append(f"gold: {exc}")
                    gold = {"status": "error", "error": str(exc)}
    except Exception as exc:
        logger.exception("[ETL] Could not open warehouse connection")
        errors.append(f"connection: {exc}")

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    status = "ok" if not errors else "error"

    summary = {
        "status": status,
        "elapsed_ms": elapsed_ms,
        "bronze": bronze,
        "silver": silver,
        "gold": gold,
        "errors": errors,
    }

    if status == "ok":
        gold_rows = gold.get("rows_out", {})
        logger.info(
            "[SUCCESS] ETL completed elapsed_ms=%s gold_daily=%s gold_artists=%s gold_tracks=%s",
            elapsed_ms,
            gold_rows.get("agg_daily_streams"),
            gold_rows.get("agg_artist_growth"),
            gold_rows.get("agg_tracks_populares"),
        )
    else:
        logger.error("[FAILURE] ETL completed with errors errors=%s", errors)

    return summary


run_full_pipeline = run_full_etl


def main() -> int:
    import json
    import sys

    from app.core.logging import setup_logging

    setup_logging()
    outcome = run_full_etl()
    print(json.dumps(outcome, indent=2, default=str))
    return 0 if outcome.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
