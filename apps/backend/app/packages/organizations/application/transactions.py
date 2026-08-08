"""DuckDB transaction helpers for multi-write use cases."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import duckdb

from app.core.database import transactional


@contextmanager
def transaction(conn: duckdb.DuckDBPyConnection) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Begin/commit/rollback via the shared serialized transactional helper."""
    with transactional(conn) as locked:
        yield locked
