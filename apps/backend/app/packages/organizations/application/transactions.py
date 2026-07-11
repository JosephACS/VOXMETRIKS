"""DuckDB transaction helpers for multi-write use cases."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import duckdb


@contextmanager
def transaction(conn: duckdb.DuckDBPyConnection) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Begin/commit/rollback on the shared connection (no nested connections)."""
    conn.execute("BEGIN TRANSACTION")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
