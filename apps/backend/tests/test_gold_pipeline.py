"""Tests for Gold layer ETL."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.etl.connection import etl_connection
from app.etl.pipelines import run_full_etl


@pytest.fixture()
def gold_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gold_test.duckdb"
    conn = duckdb.connect(str(db_path))

    conn.execute(
        """
        CREATE TABLE raw_spotify (
            id INTEGER, track_id VARCHAR, track_name VARCHAR, artists VARCHAR,
            album_name VARCHAR, popularity INTEGER, duration_ms INTEGER,
            explicit BOOLEAN, danceability DOUBLE, energy DOUBLE,
            key_col INTEGER, loudness DOUBLE, mode_col INTEGER,
            speechiness DOUBLE, acousticness DOUBLE, instrumentalness DOUBLE,
            liveness DOUBLE, valence DOUBLE, tempo DOUBLE, time_signature INTEGER,
            track_genre VARCHAR, fecha_ingesta TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO raw_spotify VALUES
        (1, 't1', 'Track One', 'Artist A', 'Album', 80, 180000, false,
         0.5, 0.8, 0, -5.0, 1, 0.04, 0.1, 0.0, 0.1, 0.5, 120.0, 4, 'pop', now())
        """
    )
    conn.execute("CREATE TABLE dim_genero (id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR)")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'pop')")
    conn.execute(
        """
        CREATE TABLE dim_artista (id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR)
        """
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist A')")
    conn.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR, nombre_track VARCHAR,
            id_artista INTEGER, id_genero INTEGER, popularity INTEGER, energy DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO dim_track VALUES (1, 't1', 'Track One', 1, 1, 80, 0.8)")
    conn.execute(
        """
        CREATE TABLE dim_usuario (
            id_usuario INTEGER PRIMARY KEY, nombre VARCHAR, email VARCHAR,
            pais VARCHAR, plan VARCHAR, fecha_registro TIMESTAMP
        )
        """
    )
    conn.execute("INSERT INTO dim_usuario VALUES (1, 'U1', 'a@test.com', 'CO', 'premium', now())")
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            id_playlist INTEGER, streams INTEGER, duracion_ms INTEGER,
            completado BOOLEAN, fecha_evento TIMESTAMP, skipped BOOLEAN,
            device_type VARCHAR, platform VARCHAR, session_id INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO fact_streaming VALUES
        (1, 1, 1, NULL, 2, 180000, true, '2026-06-01 10:00:00', false, 'mobile', 'web', 100),
        (2, 1, 1, NULL, 1, 90000, false, '2026-06-01 11:00:00', true, 'mobile', 'web', 100),
        (3, 1, 1, NULL, 1, 200000, true, '2026-06-08 09:00:00', false, 'desktop', 'web', 101)
        """
    )
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(db_path)
    get_settings.cache_clear()
    yield db_path
    restore_session_db()


def test_run_gold_pipeline(gold_db):
    full = run_full_etl()
    assert full["status"] == "ok"
    gold = full["gold"]
    assert gold["status"] == "ok"
    rows = gold["rows_out"]
    assert rows["agg_daily_streams"] >= 1
    assert rows["agg_tracks_populares"] >= 1
    assert rows["agg_user_engagement"] >= 1

    with etl_connection() as conn:
        daily = conn.execute("SELECT skip_rate FROM agg_daily_streams LIMIT 1").fetchone()
        assert daily is not None
        segments = conn.execute("SELECT segment FROM agg_user_engagement").fetchall()
        assert len(segments) >= 1
