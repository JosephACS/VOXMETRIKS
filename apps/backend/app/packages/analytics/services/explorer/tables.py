"""Warehouse table listing and row preview for Data Explorer."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import duckdb

from app.core.query_helpers import count_rows

from .security import (
    EXPLORER_BLOCKED_TABLES,
    SENSITIVE_COLUMN_NAMES,
    explorer_visible_tables,
    redact_cell,
    table_kind,
)

logger = logging.getLogger(__name__)


def get_warehouse_tables(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for name in explorer_visible_tables(conn):
        kind = table_kind(name)
        row_count = count_rows(conn, name)
        columns: List[Dict[str, str]] = []
        try:
            desc = conn.execute(f'DESCRIBE "{name}"').fetchall()
            columns = [{"name": r[0], "type": str(r[1])} for r in desc]
        except Exception:
            logger.exception("get_warehouse_tables: DESCRIBE failed for table %s", name)
        result.append({
            "name": name,
            "kind": kind,
            "layer": "gold" if kind in ("dimension", "fact", "aggregation") else "warehouse",
            "row_count": row_count,
            "columns": columns,
        })
    return result


def get_table_preview(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    page: int = 1,
    limit: int = 50,
) -> Dict[str, Any]:
    """Preview a sample page only — never stream the full table to the client."""
    allowed = set(explorer_visible_tables(conn))
    if table_name not in allowed:
        if table_name in EXPLORER_BLOCKED_TABLES:
            raise ValueError(f"Table '{table_name}' is not accessible")
        raise ValueError(f"Table '{table_name}' not found")

    # Hard cap: sample pages of 50 or 100 max (route also enforces).
    limit = 100 if limit >= 100 else 50 if limit >= 50 else max(1, min(limit, 50))
    offset = max(0, (page - 1) * limit)
    total = count_rows(conn, table_name)

    rows_raw = conn.execute(
        f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?',
        [limit, offset],
    ).fetchall()
    cols = [d[0] for d in conn.description]
    safe_cols = [c for c in cols if c.lower() not in SENSITIVE_COLUMN_NAMES]
    if not safe_cols:
        safe_cols = cols
    rows = []
    for r in rows_raw:
        item: Dict[str, Any] = {}
        for col, val in zip(cols, r):
            if col.lower() in SENSITIVE_COLUMN_NAMES:
                continue
            if val is None:
                item[col] = None
            elif hasattr(val, "isoformat"):
                item[col] = val.isoformat()
            else:
                item[col] = redact_cell(col, val)
        rows.append(item)

    col_list = ", ".join(safe_cols[:8]) if safe_cols else "*"
    query = f"SELECT {col_list}\nFROM {table_name}\nLIMIT {limit}\nOFFSET {offset};"

    return {
        "table": table_name,
        "total": total,
        "page": page,
        "limit": limit,
        "columns": safe_cols if safe_cols else cols,
        "rows": rows,
        "query": query,
    }
