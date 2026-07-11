from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Generator

import duckdb

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_write_lock = threading.Lock()


@contextmanager
def etl_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Writable DuckDB connection for ETL pipelines (separate from read-only API pool)."""
    _release_api_connections()
    settings = get_settings()
    db_path = settings.db_path_resolved
    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB warehouse not found: {db_path}. Run the legacy ELT first or create the file."
        )
    with _write_lock:
        conn = duckdb.connect(str(db_path), read_only=False)
        try:
            logger.debug("etl_connection_open path=%s", db_path)
            yield conn
        finally:
            conn.close()
            logger.debug("etl_connection_closed path=%s", db_path)


def _release_api_connections() -> None:
    """Close read-only singletons so ETL can acquire a write lock on DuckDB."""
    try:
        from app.core.database import close_read_pool
        from app.db.duckdb_client import shutdown_duckdb_client

        shutdown_duckdb_client()
        close_read_pool()
    except Exception as exc:
        logger.debug("release_api_connections skipped: %s", exc)


def execute_ddl(conn: duckdb.DuckDBPyConnection, sql: str) -> None:
    conn.execute(sql)


def count_rows(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
