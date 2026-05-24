"""
backend/services/base_service.py
================================
Generic query helpers used by all service modules.
All SQL uses only columns verified against the live DuckDB schema.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from ..database import get_table_columns, table_exists

logger = logging.getLogger("voxmetrik.service")


def fetch_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    *,
    columns: Optional[List[str]] = None,
    where: str = "",
    order_by: str = "",
    limit: int = 0,
    offset: int = 0,
    params: Optional[list] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Safe SELECT against *table*.

    - Verifies table exists.
    - Filters *columns* to those that actually exist in the schema.
    - Returns (list_of_dicts, list_of_column_names).
    """
    if not table_exists(conn, table):
        raise ValueError(
            f"Table '{table}' does not exist in the database. "
            "Run the ELT pipeline first."
        )

    real_cols = get_table_columns(conn, table)

    if columns is None or columns == ["*"]:
        cols_sql  = "*"
        used_cols = real_cols
    else:
        valid = [c for c in columns if c in real_cols]
        if not valid:
            raise ValueError(
                f"Columns {columns} do not exist in '{table}'. "
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
    if offset > 0:
        sql += f" OFFSET {offset}"

    logger.debug(f"SQL: {sql}  params={params}")
    rows = conn.execute(sql, params or []).fetchall()
    col_names = real_cols if cols_sql == "*" else used_cols
    return [dict(zip(col_names, row)) for row in rows], col_names


def count_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    where: str = "",
    params: Optional[list] = None,
) -> int:
    """Return COUNT(*) from *table* with optional WHERE clause."""
    sql = f"SELECT COUNT(*) FROM {table}"
    if where:
        sql += f" WHERE {where}"
    return conn.execute(sql, params or []).fetchone()[0]
