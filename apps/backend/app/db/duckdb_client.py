from __future__ import annotations

import re
import threading
import time
from typing import Any

import duckdb
import pandas as pd

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
db_logger = get_logger("voxmetrik.database")

_UNSAFE_SQL = re.compile(
    r"(;\s*(drop|delete|insert|update|alter|create|truncate)\b)|(--)|(/\*)",
    re.IGNORECASE,
)

_client: DuckDBClient | None = None
_client_lock = threading.Lock()


class DuckDBClient:
    """Singleton DuckDB client — borrows the process shared connection."""

    def __init__(self, db_path: str, *, read_only: bool = True) -> None:
        self._db_path = db_path
        # Kept for API compatibility; connection mode is owned by database.py.
        self._read_only = read_only
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.Lock()

    @property
    def db_path(self) -> str:
        return self._db_path

    @property
    def is_connected(self) -> bool:
        return self._conn is not None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Attach to the shared warehouse connection (never open a second handle)."""
        from app.core.database import get_connection

        with self._lock:
            if self._conn is None:
                logger.info(
                    "Opening DuckDB connection path=%s read_only=%s (shared pool)",
                    self._db_path,
                    self._read_only,
                )
                self._conn = get_connection()
            return self._conn

    def close(self) -> None:
        """Detach this client; the shared pool stays open until close_read_pool()."""
        with self._lock:
            if self._conn is not None:
                self._conn = None
                logger.info("DuckDB connection closed")

    def _validate_sql(self, sql: str) -> str:
        cleaned = sql.strip()
        if not cleaned:
            raise ValueError("Empty SQL statement")
        if _UNSAFE_SQL.search(cleaned):
            raise ValueError("Unsafe SQL pattern detected")
        return cleaned

    def execute_query(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "query",
    ) -> Any:
        safe_sql = self._validate_sql(sql)
        bound = list(params or [])
        start = time.perf_counter()
        try:
            # LockedConn.execute materializes rows under the shared DB lock.
            result = self.connect().execute(safe_sql, bound)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            db_logger.info(
                "sql label=%s elapsed_ms=%s params=%s",
                label,
                elapsed_ms,
                bound,
            )
            logger.debug("sql label=%s elapsed_ms=%s params=%s", label, elapsed_ms, bound)
            return result
        except Exception as exc:
            logger.error("sql_failed label=%s error=%s", label, exc, exc_info=True)
            raise

    def fetch_all(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "fetch_all",
    ) -> list[dict[str, Any]]:
        cursor = self.execute_query(sql, params, label=label)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def fetch_one(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "fetch_one",
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(sql, params, label=label)
        return rows[0] if rows else None

    def fetch_scalar(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "fetch_scalar",
    ) -> Any:
        cursor = self.execute_query(sql, params, label=label)
        row = cursor.fetchone()
        return row[0] if row else None

    def fetch_df(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "fetch_df",
    ) -> pd.DataFrame:
        cursor = self.execute_query(sql, params, label=label)
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=cols)

    def list_tables(self) -> list[str]:
        return [r[0] for r in self.connect().execute("SHOW TABLES").fetchall()]

    def ping(self) -> bool:
        try:
            self.fetch_scalar("SELECT 1", label="ping")
            return True
        except Exception:
            return False


def get_duckdb_client(*, force_new: bool = False) -> DuckDBClient:
    """Return process-wide DuckDB client singleton (lazy initialization)."""
    global _client
    if _client is not None and not force_new:
        return _client
    with _client_lock:
        if _client is not None and not force_new:
            return _client
        settings = get_settings()
        db_path = settings.db_path_resolved
        if not db_path.exists():
            raise FileNotFoundError(f"DuckDB warehouse not found: {db_path}")
        _client = DuckDBClient(str(db_path), read_only=True)
        _client.connect()
        return _client


def shutdown_duckdb_client() -> None:
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
            _client = None
