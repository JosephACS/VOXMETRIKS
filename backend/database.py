"""
backend/database.py
===================
DuckDB connection management for FastAPI.

Key features:
  - Thread-local read-only connections (safe for async FastAPI workers)
  - Automatic corruption recovery (same logic as pipeline)
  - Schema introspection: get_table_columns() returns REAL column names
  - Dependency injection: get_conn() for use in route dependencies
"""

from __future__ import annotations

import logging
import shutil
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List

import duckdb

from .config import get_settings

logger = logging.getLogger("voxmetrik.database")

# Thread-local storage for per-thread connections
_local = threading.local()


def _open_read_only(db_path: Path, *, recreate: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Open a read-only DuckDB connection.
    If the file is corrupt/version-mismatched, log an error and raise.
    (Read-only mode cannot recreate; recreation is the pipeline's job.)
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {db_path}\n"
            "  → Run python elt_pipeline.py first to create the database."
        )
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        conn.execute("SELECT 1").fetchone()  # smoke test
        return conn
    except Exception as exc:
        err_str = str(exc).lower()
        if any(kw in err_str for kw in ("serial", "deserial", "incompatible", "version")):
            raise RuntimeError(
                f"DuckDB serialization/version error: {exc}\n"
                "  → Run python elt_pipeline.py to recreate the database."
            ) from exc
        raise


def get_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    FastAPI dependency: yields a thread-local read-only DuckDB connection.
    Each thread keeps its own connection alive for the server lifetime.
    """
    settings = get_settings()
    db_path  = settings.db_path_resolved

    if not hasattr(_local, "conn") or _local.conn is None:
        logger.debug(f"Opening DuckDB connection (thread {threading.get_ident()})")
        _local.conn = _open_read_only(db_path)

    try:
        yield _local.conn
    except Exception:
        # On error, drop the connection so the next request gets a fresh one
        try:
            _local.conn.close()
        except Exception:
            pass
        _local.conn = None
        raise


# ── Schema introspection ──────────────────────────────────────────────────────

def get_table_columns(
    conn: duckdb.DuckDBPyConnection, table: str
) -> List[str]:
    """
    Return the actual column names for *table* from DuckDB's DESCRIBE output.
    Raises ValueError if the table does not exist.
    """
    try:
        rows = conn.execute(f"DESCRIBE {table}").fetchall()
        return [row[0] for row in rows]
    except Exception as exc:
        raise ValueError(f"Cannot describe table '{table}': {exc}") from exc


def list_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    """Return the names of all user tables in the database."""
    rows = conn.execute("SHOW TABLES").fetchall()
    return [row[0] for row in rows]


def table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    """Check whether a table exists in the database."""
    return table in list_tables(conn)


def safe_query(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    select_cols: List[str],
    where: str = "",
    order_by: str = "",
    limit: int = 0,
    params: list | None = None,
) -> list:
    """
    Execute a parameterized SELECT against *table*, automatically filtering
    *select_cols* to only those that actually exist in the table schema.

    Args:
        conn:        DuckDB connection.
        table:       Table name.
        select_cols: Desired columns.  '*' is accepted to select all.
        where:       Optional WHERE clause (without the 'WHERE' keyword).
        order_by:    Optional ORDER BY clause.
        limit:       Optional LIMIT (0 = no limit).
        params:      Positional parameters for the WHERE clause.

    Returns:
        List of dicts (column → value).
    """
    real_cols = get_table_columns(conn, table)

    if select_cols == ["*"]:
        cols_sql = "*"
        used_cols = real_cols
    else:
        valid = [c for c in select_cols if c in real_cols]
        if not valid:
            raise ValueError(
                f"None of the requested columns {select_cols} exist in '{table}'. "
                f"Available: {real_cols}"
            )
        cols_sql  = ", ".join(valid)
        used_cols = valid

    sql = f"SELECT {cols_sql} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit > 0:
        sql += f" LIMIT {limit}"

    rows = conn.execute(sql, params or []).fetchall()
    return [dict(zip(used_cols if cols_sql != "*" else real_cols, row)) for row in rows]
