from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.connection import count_rows

logger = get_logger(__name__)


def table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return table.lower() in {
        r[0].lower() for r in conn.execute("SHOW TABLES").fetchall()
    }


def rebuild_table(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    ddl: str,
    insert_sql: str,
    *,
    label: str,
) -> int:
    logger.info("[GOLD] Building %s...", label)
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(ddl)
    conn.execute(insert_sql)
    rows = count_rows(conn, table)
    logger.info("[GOLD] %s → %s rows", table, f"{rows:,}")
    return rows


def stream_events_table(conn: duckdb.DuckDBPyConnection) -> str:
    """Prefer cleaned silver streams; fall back to fact_streaming."""
    if table_exists(conn, "silver_streams"):
        return "silver_streams"
    return "fact_streaming"


def stream_events_all_table(conn: duckdb.DuckDBPyConnection) -> str:
    """Full event log including skipped (for skip_rate / platform)."""
    if table_exists(conn, "fact_streaming"):
        return "fact_streaming"
    return stream_events_table(conn)
