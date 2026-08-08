# -*- coding: utf-8 -*-
"""Spec 047 — backend lifespan succeeds without warehouse gold tables."""

from __future__ import annotations

import duckdb
from fastapi.testclient import TestClient

from tests.db_isolation import bind_test_db, restore_session_db


def test_lifespan_without_dim_track_starts(tmp_path):
    from app.core import schema_bootstrap
    from app.core.database import close_read_pool, table_exists, using_write_conn
    from app.core.schema_bootstrap import reset_schema_ready_for_tests
    from app.db.duckdb_client import shutdown_duckdb_client

    db_path = tmp_path / "empty_app.duckdb"
    duckdb.connect(str(db_path)).close()

    previous_ready = schema_bootstrap._schema_ready
    reset_schema_ready_for_tests()
    bind_test_db(db_path)
    shutdown_duckdb_client()
    close_read_pool()

    try:
        from app.main import create_app

        application = create_app()
        with TestClient(application) as client:
            health = client.get("/health")
            assert health.status_code == 200

            paths = {getattr(r, "path", "") for r in application.routes}
            assert any("/artist-space" in p for p in paths)
            assert any("/workpanel" in p for p in paths)
            assert any("/reports/simple/catalog" in p for p in paths)

        with using_write_conn() as conn:
            assert not table_exists(conn, "dim_track")
            if table_exists(conn, "app_favorite"):
                assert int(conn.execute("SELECT COUNT(*) FROM app_favorite").fetchone()[0]) == 0
            if table_exists(conn, "app_playlist"):
                assert int(conn.execute("SELECT COUNT(*) FROM app_playlist").fetchone()[0]) == 0
    finally:
        schema_bootstrap._schema_ready = previous_ready
        shutdown_duckdb_client()
        close_read_pool()
        restore_session_db()
