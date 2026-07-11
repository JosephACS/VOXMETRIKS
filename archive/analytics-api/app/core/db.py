from __future__ import annotations

import re
import threading
import time
from contextlib import contextmanager
from typing import Any, Generator

import duckdb

from app.core.cache import cached_call
from app.core.config import get_settings
from app.core.exceptions import QueryError
from app.core.logging_config import get_logger

logger = get_logger("voxmetrik.analytics.db")

_read_lock = threading.Lock()
_read_conn: duckdb.DuckDBPyConnection | None = None

_UNSAFE_SQL = re.compile(
    r"(;\s*(drop|delete|insert|update|alter|create|truncate)\b)|(--)|(/\*)",
    re.IGNORECASE,
)


def _resolve_db_path():
    settings = get_settings()
    db_path = settings.db_path_resolved
    if not db_path.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {db_path}. "
            "Run the ELT pipeline to create data/warehouse/voxmetrik.duckdb."
        )
    return db_path


def validate_sql(sql: str) -> str:
    cleaned = sql.strip()
    if not cleaned:
        raise QueryError("Empty SQL statement", code="SQL_EMPTY")
    if _UNSAFE_SQL.search(cleaned):
        raise QueryError("Unsafe SQL pattern detected", code="SQL_UNSAFE")
    return cleaned


def open_db() -> None:
    global _read_conn
    if _read_conn is not None:
        return
    db_path = _resolve_db_path()
    _read_conn = duckdb.connect(str(db_path), read_only=True)
    logger.info("DuckDB read connection opened path=%s", db_path)


def close_db() -> None:
    global _read_conn
    if _read_conn is None:
        return
    try:
        _read_conn.close()
    except Exception:
        logger.warning("Failed to close DuckDB connection", exc_info=True)
    _read_conn = None
    logger.info("DuckDB read connection closed")


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    if _read_conn is None:
        open_db()
    assert _read_conn is not None
    with _read_lock:
        yield _read_conn


@contextmanager
def db_session() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    if _read_conn is not None:
        with _read_lock:
            yield _read_conn
        return
    db_path = _resolve_db_path()
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        yield conn
    finally:
        conn.close()


def _run_query(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | tuple | None,
    label: str,
) -> tuple[list[str], list[tuple], float]:
    safe_sql = validate_sql(sql)
    bound = list(params or [])
    settings = get_settings()
    start = time.perf_counter()
    try:
        cursor = conn.execute(safe_sql, bound)
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        if settings.sql_log_enabled:
            logger.info(
                "sql_executed label=%s elapsed_ms=%s rows=%s params=%s",
                label,
                elapsed_ms,
                len(rows),
                bound,
                extra={"sql_label": label, "elapsed_ms": elapsed_ms, "params": bound, "row_count": len(rows)},
            )
        return cols, rows, elapsed_ms
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "sql_failed label=%s elapsed_ms=%s error=%s",
            label,
            elapsed_ms,
            exc,
            exc_info=True,
        )
        raise QueryError(f"Query failed [{label}]: {exc}", code="SQL_EXECUTION_ERROR") from exc


def fetch_all(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | tuple | None = None,
    *,
    label: str = "fetch_all",
    use_cache: bool = False,
) -> list[dict]:
    def _execute() -> list[dict]:
        cols, rows, _ = _run_query(conn, sql, params, label)
        return [dict(zip(cols, row)) for row in rows]

    if use_cache:
        return cached_call(label, _execute, sql, list(params or []))
    return _execute()


def fetch_one(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | tuple | None = None,
    *,
    label: str = "fetch_one",
    use_cache: bool = False,
) -> dict | None:
    rows = fetch_all(conn, sql, params, label=label, use_cache=use_cache)
    return rows[0] if rows else None


def fetch_scalar(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | tuple | None = None,
    *,
    label: str = "fetch_scalar",
) -> Any:
    _, rows, _ = _run_query(conn, sql, params, label)
    return rows[0][0] if rows else None


def measure_latency(conn: duckdb.DuckDBPyConnection, sql: str, label: str) -> float:
    start = time.perf_counter()
    conn.execute(validate_sql(sql)).fetchone()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.debug("latency_probe label=%s elapsed_ms=%s", label, elapsed_ms)
    return elapsed_ms
