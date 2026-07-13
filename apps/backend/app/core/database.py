"""
backend/database.py
===================
DuckDB connection management for FastAPI.

DuckDB forbids opening the same file with mixed configs (e.g. read_only=True
while a read-write connection exists). All access goes through one shared
read-write connection serialized by ``_db_lock``.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List

import duckdb

from .config import get_settings

logger = logging.getLogger("voxmetrik.database")

# Serializes connect + every SQL execute on the shared handle.
_db_lock = threading.RLock()
_shared_conn: duckdb.DuckDBPyConnection | None = None


class _MaterializedResult:
    """Snapshot of a DuckDB query result (safe after the DB lock is released)."""

    __slots__ = ("description", "_rows", "_i")

    def __init__(self, description: Any, rows: list) -> None:
        self.description = description
        self._rows = rows
        self._i = 0

    def fetchall(self) -> list:
        return list(self._rows)

    def fetchone(self) -> Any:
        if self._i >= len(self._rows):
            return None
        row = self._rows[self._i]
        self._i += 1
        return row

    def fetchmany(self, size: int = 1) -> list:
        chunk = self._rows[self._i : self._i + size]
        self._i += len(chunk)
        return list(chunk)

    def df(self) -> Any:
        import pandas as pd

        cols = [d[0] for d in (self.description or [])]
        return pd.DataFrame(self._rows, columns=cols or None)


class _LockedConn:
    """Proxy that serializes DuckDB calls without holding a lock across FastAPI yields.

    FastAPI resumes dependency cleanup on a *different* worker thread than enter,
    so ``with _db_lock: yield conn`` raises ``cannot release un-acquired lock``.

    Results are materialized under the lock so ``.fetchall()`` is safe afterwards.
    """

    __slots__ = ("_conn",)

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003
        with _db_lock:
            result = self._conn.execute(*args, **kwargs)
            try:
                rows = result.fetchall()
            except Exception:
                # DDL / statements with no result set
                rows = []
            description = getattr(result, "description", None)
            return _MaterializedResult(description, rows)

    def executemany(self, *args, **kwargs):  # noqa: ANN002, ANN003
        with _db_lock:
            return self._conn.executemany(*args, **kwargs)

    def cursor(self, *args, **kwargs):  # noqa: ANN002, ANN003
        with _db_lock:
            return self._conn.cursor(*args, **kwargs)

    def commit(self, *args, **kwargs):  # noqa: ANN002, ANN003
        with _db_lock:
            return self._conn.commit(*args, **kwargs)

    def rollback(self, *args, **kwargs):  # noqa: ANN002, ANN003
        with _db_lock:
            return self._conn.rollback(*args, **kwargs)

    def close(self) -> None:
        # Shared pool owns the real connection lifetime.
        return None

    def __getattr__(self, name: str):
        attr = getattr(self._conn, name)
        if callable(attr):

            def _guarded(*args, **kwargs):  # noqa: ANN002, ANN003
                with _db_lock:
                    return attr(*args, **kwargs)

            return _guarded
        return attr


def _db_path() -> Path:
    return get_settings().db_path_resolved


def _ensure_shared_conn(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open the process-wide connection if needed (caller must hold ``_db_lock``)."""
    global _shared_conn
    path = db_path or _db_path()
    if not path.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {path}\n"
            "  → Run python elt_pipeline.py first to create the database."
        )
    if _shared_conn is None:
        # Single RW connection — never mix with a separate read_only handle.
        _shared_conn = duckdb.connect(str(path))
        logger.info("Read pool opened (shared read-write connection)")
    return _shared_conn


def _borrow_conn() -> _LockedConn:
    with _db_lock:
        return _LockedConn(_ensure_shared_conn())


def open_read_pool(db_path: Path) -> None:
    """Open the shared DuckDB connection for the process lifetime."""
    with _db_lock:
        _ensure_shared_conn(db_path)


def close_read_pool() -> None:
    """Close the shared connection on shutdown."""
    global _shared_conn
    with _db_lock:
        if _shared_conn is None:
            return
        try:
            _shared_conn.close()
        except Exception:
            logger.warning("close_read_pool: failed to close shared connection", exc_info=True)
        _shared_conn = None
        logger.info("Read pool closed")


def get_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    FastAPI dependency: yields a lock-safe proxy to the shared connection.

    Must not hold ``_db_lock`` across ``yield`` (threadpool enter/exit mismatch).
    """
    yield _borrow_conn()  # type: ignore[misc]


def _shutdown_aux_clients() -> None:
    """Close other DuckDB handles that would conflict with this process connection."""
    try:
        from app.db.duckdb_client import shutdown_duckdb_client

        shutdown_duckdb_client()
    except Exception:
        logger.debug("aux client shutdown skipped", exc_info=True)


def _release_read_connections() -> None:
    """
    Legacy hook used by tests before exclusive writes.

    With a single shared RW connection there is nothing to tear down for mode
    switching; still shut down auxiliary clients that may have opened the file.
    """
    _shutdown_aux_clients()


def _reopen_read_pool() -> None:
    """Legacy hook — ensure the shared pool is available after a write section."""
    try:
        with _db_lock:
            _ensure_shared_conn()
    except Exception:
        logger.debug("reopen_read_pool skipped", exc_info=True)


@contextmanager
def using_write_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Yield a lock-safe proxy for writes (same-thread context manager is fine)."""
    _shutdown_aux_clients()
    yield _borrow_conn()  # type: ignore[misc]


def get_write_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """FastAPI dependency: lock-safe shared connection for writes."""
    _shutdown_aux_clients()
    yield _borrow_conn()  # type: ignore[misc]


# ── Schema introspection ──────────────────────────────────────────────────────

def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a lock-safe proxy to the shared warehouse connection."""
    return _borrow_conn()  # type: ignore[return-value]


def fetch_all_rows(conn: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> list[dict]:
    rows = conn.execute(sql, params or []).fetchall()
    cols = [d[0] for d in conn.description]
    return [dict(zip(cols, row)) for row in rows]


def fetch_one_row(conn: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> dict | None:
    rows = fetch_all_rows(conn, sql, params)
    return rows[0] if rows else None


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
        cols_sql = ", ".join(valid)
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
