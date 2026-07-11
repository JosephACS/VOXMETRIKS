from __future__ import annotations

from app.db.duckdb_client import DuckDBClient


def table_exists(client: DuckDBClient, table: str) -> bool:
    return table.lower() in {t.lower() for t in client.list_tables()}


def normalize_skip_rate(value: float | int | None) -> float:
    """Convert skip_rate from percentage (0–100) or fraction (0–1) to fraction."""
    if value is None:
        return 0.0
    rate = float(value)
    if rate > 1.0:
        return round(rate / 100.0, 4)
    return round(rate, 4)


def table_column_names(client: DuckDBClient, table: str) -> set[str]:
    if not table_exists(client, table):
        return set()
    rows = client.connect().execute(f"DESCRIBE {table}").fetchall()
    return {str(r[0]).lower() for r in rows}


def agg_daily_skip_rate_sql(client: DuckDBClient) -> str:
    """SQL expression for skip rate — supports ELT skip_count and boot skip_rate columns."""
    cols = table_column_names(client, "agg_daily_streams")
    if "skip_rate" in cols:
        return "skip_rate"
    if "skip_count" in cols:
        return "ROUND(COALESCE(skip_count, 0) * 1.0 / NULLIF(total_streams, 0), 4)"
    return "0.0"


def agg_daily_skip_count_sql(client: DuckDBClient) -> str:
    """SQL expression for skip count — derived from skip_rate when only that column exists."""
    cols = table_column_names(client, "agg_daily_streams")
    if "skip_count" in cols:
        return "skip_count"
    if "skip_rate" in cols:
        return "CAST(ROUND(COALESCE(skip_rate, 0) * total_streams) AS INTEGER)"
    return "0"
