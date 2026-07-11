from __future__ import annotations

from typing import Generator

import duckdb

from app.db.duckdb_client import get_duckdb_client


def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """FastAPI dependency — yields shared DuckDB connection from singleton client."""
    client = get_duckdb_client()
    yield client.connect()
