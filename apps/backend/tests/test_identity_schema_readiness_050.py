"""T002 — identity schema readiness is per database, not process-global."""

from __future__ import annotations

from pathlib import Path

import duckdb

from app.core.database import table_exists
from app.core.schema_bootstrap import mark_schema_ready, reset_schema_ready_for_tests, schema_ready
from app.packages.identity.services.user_storage import ensure_user_tables


def test_ensure_user_tables_creates_app_user_on_second_independent_database(tmp_path: Path) -> None:
    reset_schema_ready_for_tests()
    first = duckdb.connect(str(tmp_path / "first.duckdb"))
    ensure_user_tables(first)
    assert table_exists(first, "app_user")
    mark_schema_ready()
    assert schema_ready() is True
    first.close()

    second = duckdb.connect(str(tmp_path / "second.duckdb"))
    ensure_user_tables(second)
    assert table_exists(second, "app_user")
    second.execute("SELECT id FROM app_user LIMIT 1")
    second.close()


def test_ensure_user_tables_is_idempotent_on_the_same_database(tmp_path: Path) -> None:
    reset_schema_ready_for_tests()
    path = tmp_path / "same.duckdb"
    conn = duckdb.connect(str(path))
    ensure_user_tables(conn)
    ensure_user_tables(conn)
    assert table_exists(conn, "app_user")
    conn.close()


def test_fresh_memory_connection_is_not_skipped_by_another_memory_connection() -> None:
    reset_schema_ready_for_tests()
    a = duckdb.connect(":memory:")
    ensure_user_tables(a)
    mark_schema_ready()
    b = duckdb.connect(":memory:")
    ensure_user_tables(b)
    assert table_exists(b, "app_user")
    a.close()
    b.close()
