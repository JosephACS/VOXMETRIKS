"""Data explorer security rules and table metadata helpers."""

from __future__ import annotations

from typing import Any, List

import duckdb

EXPLORER_BLOCKED_TABLES: frozenset[str] = frozenset({
    "app_user",
    "app_session",
})

SENSITIVE_COLUMN_NAMES: frozenset[str] = frozenset({
    "password_hash",
    "password",
    "token",
    "session_token",
})


def table_kind(name: str) -> str:
    if name.startswith("dim_"):
        return "dimension"
    if name.startswith("fact_"):
        return "fact"
    if name.startswith("agg_"):
        return "aggregation"
    if name.startswith("ctl_") or name == "raw_spotify":
        return "control"
    if name.startswith("app_"):
        return "application"
    return "other"


def allowed_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()
    return [r[0] for r in rows]


def explorer_visible_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    return [n for n in allowed_tables(conn) if n not in EXPLORER_BLOCKED_TABLES]


def redact_cell(column: str, value: Any) -> Any:
    if column.lower() in SENSITIVE_COLUMN_NAMES:
        return "***"
    return value
