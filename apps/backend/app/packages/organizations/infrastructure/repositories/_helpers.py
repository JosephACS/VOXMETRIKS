"""Shared repository helpers."""

from __future__ import annotations

import duckdb

from app.packages.organizations.domain.errors import DuplicateError, PersistenceError


def next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def raise_persistence(exc: Exception, *, action: str) -> None:
    msg = str(exc).lower()
    if "unique" in msg or "constraint" in msg or "duplicate" in msg:
        raise DuplicateError(f"{action}: {exc}") from exc
    raise PersistenceError(f"{action}: {exc}") from exc
