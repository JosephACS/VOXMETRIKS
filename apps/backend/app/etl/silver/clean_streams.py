from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.connection import count_rows, execute_ddl

logger = get_logger(__name__)

SILVER_STREAMS_DDL = """
CREATE TABLE IF NOT EXISTS silver_streams (
    id_streaming      INTEGER PRIMARY KEY,
    id_track          INTEGER NOT NULL,
    id_usuario        INTEGER,
    id_playlist       INTEGER,
    streams           INTEGER,
    duracion_ms       INTEGER,
    completado        BOOLEAN,
    device_type       VARCHAR,
    platform          VARCHAR,
    fecha_evento      TIMESTAMP,
    fecha_limpia      DATE,
    engagement_score  DOUBLE,
    cleaned_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def clean_streams(conn: duckdb.DuckDBPyConnection, *, source_table: str = "fact_streaming") -> dict:
    """Transform fact_streaming → silver_streams (non-skipped events only)."""
    logger.info("[SILVER] Cleaning streams %s → silver_streams", source_table)

    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if source_table not in tables:
        raise RuntimeError(f"Source table '{source_table}' not found")

    execute_ddl(conn, SILVER_STREAMS_DDL)

    conn.execute("DELETE FROM silver_streams")

    conn.execute(
        f"""
        INSERT INTO silver_streams (
            id_streaming, id_track, id_usuario, id_playlist, streams, duracion_ms,
            completado, device_type, platform, fecha_evento, fecha_limpia,
            engagement_score, cleaned_at
        )
        SELECT
            id_streaming,
            id_track,
            id_usuario,
            id_playlist,
            streams,
            duracion_ms,
            completado,
            device_type,
            platform,
            fecha_evento,
            CAST(fecha_evento AS DATE) AS fecha_limpia,
            ROUND(
                COALESCE(streams, 0) * COALESCE(duracion_ms, 0) / 1000.0,
                4
            ) AS engagement_score,
            CURRENT_TIMESTAMP
        FROM {source_table}
        WHERE COALESCE(skipped, FALSE) = FALSE
          AND id_track IS NOT NULL
          AND fecha_evento IS NOT NULL
        """
    )

    rows_in = count_rows(conn, source_table)
    rows_out = count_rows(conn, "silver_streams")
    logger.info("[SILVER] Cleaning streams → silver_streams (%s rows)", rows_out)
    return {
        "source": source_table,
        "target": "silver_streams",
        "rows_in": rows_in,
        "rows_out": rows_out,
        "status": "ok",
    }
