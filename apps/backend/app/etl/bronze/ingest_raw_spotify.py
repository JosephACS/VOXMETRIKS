from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.bronze.bronze_loader import upsert_from_source
from app.etl.connection import count_rows

logger = get_logger(__name__)


def ingest_raw_spotify(conn: duckdb.DuckDBPyConnection, *, source_table: str = "raw_spotify") -> dict:
    """
    Bronze intake — copy raw_spotify into bronze_raw_tracks without transformation.
    Adds ingestion_timestamp at load time.
    """
    logger.info("[BRONZE] Ingesting %s → bronze_raw_tracks", source_table)
    result = upsert_from_source(conn, source_table=source_table)
    bronze_rows = result["bronze_rows"]
    logger.info(
        "[BRONZE] Ingest complete source=%s bronze_raw_tracks rows=%s",
        source_table,
        bronze_rows,
    )
    return {
        "layer": "bronze",
        "source": source_table,
        "target": "bronze_raw_tracks",
        "rows_in": result["source_rows"],
        "rows_out": bronze_rows,
        "status": "ok",
    }
