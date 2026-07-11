"""Data validation tests."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.utils.data_validation import validate_warehouse


@pytest.fixture()
def valid_db(tmp_path, monkeypatch):
    db_path = tmp_path / "valid.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE dim_track (id_track INTEGER PRIMARY KEY, nombre_track VARCHAR)")
    conn.execute("INSERT INTO dim_track VALUES (1, 'A')")
    conn.execute("CREATE TABLE dim_usuario (id_usuario INTEGER PRIMARY KEY, nombre VARCHAR)")
    conn.execute("INSERT INTO dim_usuario VALUES (1, 'U')")
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER
        )
        """
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
    conn.execute("INSERT INTO agg_daily_streams VALUES ('2026-01-01', 1, 1, 1, 100.0, 0.1)")
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, nombre_artista VARCHAR,
            popularity INTEGER, total_streams INTEGER, engagement_score DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_tracks_populares VALUES (1, 'A', 'X', 1, 1, 1.0)")
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR,
            streams_7d INTEGER, streams_30d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_artist_growth VALUES (1, 'X', 1, 1, 0.0, 1)")
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield
    shutdown_duckdb_client()
    get_settings.cache_clear()


def test_validate_warehouse_ok(valid_db):
    report = validate_warehouse()
    assert report.tables_ok is True
    assert report.gold_ready is True
    assert report.row_counts["tracks"] == 1
    assert report.healthy is True
