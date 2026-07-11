"""DuckDB helpers for smart recommendation modules."""

from __future__ import annotations

import duckdb


def table_exists_conn(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE lower(table_name) = lower(?)
            """,
            [table],
        ).fetchone()
        return bool(row and int(row[0]) > 0)
    except Exception:
        return False
