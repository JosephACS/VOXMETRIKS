"""Unit tests for hybrid recommendation engine."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.services.recommendation_service import RecommendationService


@pytest.fixture()
def rec_db(tmp_path, monkeypatch):
    db_path = tmp_path / "rec.duckdb"
    conn = duckdb.connect(str(db_path))

    conn.execute("CREATE TABLE dim_genero (id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR)")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'pop'), (2, 'rock')")
    conn.execute("CREATE TABLE dim_artista (id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR)")
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist A'), (2, 'Artist B')")
    conn.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, id_artista INTEGER,
            id_genero INTEGER, popularity INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO dim_track VALUES
        (1, 'Pop Hit', 1, 1, 90),
        (2, 'Rock Song', 2, 2, 70),
        (3, 'New Pop', 1, 1, 85)
        """
    )
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            streams INTEGER, duracion_ms INTEGER, completado BOOLEAN,
            fecha_evento TIMESTAMP, skipped BOOLEAN,
            device_type VARCHAR, platform VARCHAR
        )
        """
    )
    conn.execute(
        """
        INSERT INTO fact_streaming VALUES
        (1, 1, 1, 2, 180000, true, CURRENT_TIMESTAMP - INTERVAL 2 DAY, false, 'mobile', 'android'),
        (2, 1, 1, 1, 90000, false, CURRENT_TIMESTAMP - INTERVAL 1 DAY, true, 'mobile', 'android'),
        (3, 2, 1, 1, 200000, true, CURRENT_TIMESTAMP - INTERVAL 5 DAY, false, 'desktop', 'web')
        """
    )
    conn.execute(
        """
        CREATE TABLE silver_streams (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            streams INTEGER, duracion_ms INTEGER, engagement_score DOUBLE, fecha_evento TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO silver_streams
        SELECT id_streaming, id_track, id_usuario, streams, duracion_ms,
               streams * duracion_ms / 1000.0, fecha_evento
        FROM fact_streaming WHERE skipped = false
        """
    )
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, nombre_artista VARCHAR,
            popularity INTEGER, total_streams INTEGER, engagement_score DOUBLE
        )
        """
    )
    conn.execute(
        """
        INSERT INTO agg_tracks_populares VALUES
        (1, 'Pop Hit', 'Artist A', 90, 500, 800.0),
        (2, 'Rock Song', 'Artist B', 70, 300, 500.0),
        (3, 'New Pop', 'Artist A', 85, 450, 750.0)
        """
    )
    conn.execute(
        """
        CREATE TABLE agg_user_engagement (
            segment VARCHAR PRIMARY KEY, user_count INTEGER,
            avg_plays DOUBLE, avg_session_min DOUBLE, retention_pct DOUBLE
        )
        """
    )
    conn.execute(
        "INSERT INTO agg_user_engagement VALUES ('power_users', 1, 3.0, 8.0, 75.0)"
    )
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(db_path)
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield db_path
    shutdown_duckdb_client()
    restore_session_db()


def test_build_user_profile(rec_db):
    service = RecommendationService()
    profile = service.build_user_profile(1)
    assert profile.total_plays == 2
    assert 1 in profile.top_genres
    assert profile.top_genre_names[1] == "pop"
    assert 1 in profile.top_artists
    assert profile.preferred_device == "mobile"


def test_rank_tracks_scoring(rec_db):
    service = RecommendationService()
    items = service.rank_tracks(1, limit=3)
    assert len(items) >= 1
    assert all(0 <= item.score <= 1 for item in items)
    assert items[0].score >= items[-1].score
    assert items[0].reason
    assert items[0].track_id > 0


def test_get_recommendations_response_shape(rec_db):
    service = RecommendationService()
    resp = service.get_recommendations(1, limit=2)
    assert resp.user_id == 1
    assert resp.count == len(resp.recommendations)
    assert resp.recommendations[0].track_id > 0
