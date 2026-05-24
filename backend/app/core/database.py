"""
backend/database.py
===================
DuckDB connection management for FastAPI.

Key features:
  - Per-request connections (safe for reads and writes)
  - Automatic DB validation on startup
  - Schema introspection: get_table_columns() returns REAL column names
  - Dependency injection: get_conn() for use in route dependencies
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Dict, Generator, List

import duckdb

from .config import get_settings

logger = logging.getLogger("voxmetrik.database")

# Global write lock to serialize write operations
_write_lock = threading.Lock()


def get_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    FastAPI dependency: yields a per-request DuckDB connection.
    Opens a fresh connection for each request and closes it after.
    """
    settings = get_settings()
    db_path  = settings.db_path_resolved

    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {db_path}\n"
            "  → Run python elt_pipeline.py first to create the database."
        )

    conn = duckdb.connect(str(db_path))
    try:
        yield conn
    except Exception:
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_write_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    FastAPI dependency: yields a per-request DuckDB connection for write operations.
    Uses a write lock to prevent concurrent writes.
    """
    settings = get_settings()
    db_path  = settings.db_path_resolved

    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {db_path}\n"
            "  → Run python elt_pipeline.py first to create the database."
        )

    with _write_lock:
        conn = duckdb.connect(str(db_path))
        try:
            yield conn
        except Exception:
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass


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
