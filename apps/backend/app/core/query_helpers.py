"""Shared DuckDB query helpers (count_rows, fetch_rows) for service layers."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import duckdb


def count_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    where: str = "",
    params: list | None = None,
) -> int:
    sql = f"SELECT COUNT(*) FROM {table}"
    if where:
        sql += f" WHERE {where}"

    result = conn.execute(sql, params or []).fetchone()
    return result[0] if result else 0


def fetch_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: List[str] | None = None,
    where: str = "",
    order_by: str = "",
    limit: int = 0,
    offset: int = 0,
    params: list | None = None,
) -> Tuple[List[Dict[str, Any]], int]:
    if columns:
        cols_sql = ", ".join(columns)
    else:
        cols_sql = "*"

    sql = f"SELECT {cols_sql} FROM {table}"

    if where:
        sql += f" WHERE {where}"

    if order_by:
        sql += f" ORDER BY {order_by}"

    if limit > 0:
        sql += f" LIMIT {limit}"

    if offset > 0:
        sql += f" OFFSET {offset}"

    rows = conn.execute(sql, params or []).fetchall()

    if columns:
        result = [dict(zip(columns, row)) for row in rows]
    else:
        describe_rows = conn.execute(f"DESCRIBE {table}").fetchall()
        column_names = [row[0] for row in describe_rows]
        result = [dict(zip(column_names, row)) for row in rows]

    total = count_rows(conn, table, where=where, params=params)
    return result, total
