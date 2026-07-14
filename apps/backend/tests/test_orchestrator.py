"""Orchestrator boot tests."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.pipeline.orchestrator import get_boot_state, run_system_boot


@pytest.fixture()
def boot_db(tmp_path, monkeypatch):
    db_path = tmp_path / "boot.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE dim_track (id_track INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO dim_track VALUES (1)")
    conn.execute("CREATE TABLE dim_usuario (id_usuario INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO dim_usuario VALUES (1)")
    conn.execute(
        "CREATE TABLE fact_streaming (id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER)"
    )
    conn.execute("INSERT INTO fact_streaming VALUES (1, 1, 1)")
    conn.execute(
        """
        CREATE TABLE agg_daily_streams (
            fecha DATE PRIMARY KEY, total_streams INTEGER, unique_users INTEGER,
            unique_tracks INTEGER, avg_duration_ms DOUBLE, skip_rate DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_daily_streams VALUES ('2026-01-01', 5, 2, 1, 100.0, 0.2)")
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, nombre_artista VARCHAR,
            popularity INTEGER, total_streams INTEGER, engagement_score DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_tracks_populares VALUES (1, 'T', 'A', 1, 1, 1.0)")
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR,
            streams_7d INTEGER, streams_30d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_artist_growth VALUES (1, 'A', 1, 1, 0.0, 1)")
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("RUN_ETL_ON_BOOT", "never")
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(db_path)
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield
    shutdown_duckdb_client()
    restore_session_db()


def test_run_system_boot_skips_etl_when_gold_ready(boot_db):
    state = run_system_boot()
    assert state["completed"] is True
    assert state["etl_status"] == "skipped"
    assert get_boot_state()["gold_ready"] is True
