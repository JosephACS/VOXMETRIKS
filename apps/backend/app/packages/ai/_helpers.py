"""DuckDB helpers for AI service."""

from __future__ import annotations

import duckdb


def table_exists_conn(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [name],
        ).fetchone()
        return bool(row and row[0])
    except Exception:
        return False
