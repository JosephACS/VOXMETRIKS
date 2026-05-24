"""
backend/services/base_service.py
================================
Base utilities for service layer (count_rows, fetch_rows).
Used by track_service, artist_service, genre_service, and stats_service.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import duckdb


def count_rows(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    where: str = "",
    params: list | None = None,
) -> int:
    """
    Count rows in a table with optional WHERE clause and parameters.
    
    Args:
        conn: DuckDB connection
        table: Table name
        where: WHERE clause (without WHERE keyword)
        params: Query parameters for parameterized queries
    
    Returns:
        Number of rows matching the criteria
    """
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
    """
    Fetch rows from a table with optional filtering, ordering, and pagination.
    
    Args:
        conn: DuckDB connection
        table: Table name
        columns: List of columns to select (defaults to *)
        where: WHERE clause (without WHERE keyword)
        order_by: ORDER BY clause (without ORDER BY keyword)
        limit: LIMIT clause (0 = no limit)
        offset: OFFSET clause
        params: Query parameters for parameterized queries
    
    Returns:
        Tuple of (rows as list of dicts, total count)
    """
    # Build SELECT clause
    if columns:
        cols_sql = ", ".join(columns)
    else:
        cols_sql = "*"
    
    # Build main query
    sql = f"SELECT {cols_sql} FROM {table}"
    
    if where:
        sql += f" WHERE {where}"
    
    if order_by:
        sql += f" ORDER BY {order_by}"
    
    if limit > 0:
        sql += f" LIMIT {limit}"
    
    if offset > 0:
        sql += f" OFFSET {offset}"
    
    # Execute query
    rows = conn.execute(sql, params or []).fetchall()
    
    # Convert to list of dicts
    if columns:
        result = [dict(zip(columns, row)) for row in rows]
    else:
        # Get column names from DESCRIBE
        describe_rows = conn.execute(f"DESCRIBE {table}").fetchall()
        column_names = [row[0] for row in describe_rows]
        result = [dict(zip(column_names, row)) for row in rows]
    
    # Get total count
    total = count_rows(conn, table, where=where, params=params)
    
    return result, total
