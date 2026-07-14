"""Tests for deterministic recommendation engine scoring."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.services.recommendation_engine import RecommendationEngine
from app.services.scoring.popularity_scoring import score_popularity
from app.services.scoring.trending_boost import TrendingBoost


@pytest.fixture()
def engine_db(tmp_path, monkeypatch):
    db_path = tmp_path / "rec_engine.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE dim_genero (id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR)")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'pop')")
    conn.execute("CREATE TABLE dim_artista (id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR)")
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist A')")
    conn.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR,
            id_artista INTEGER, id_genero INTEGER, popularity INTEGER
        )
        """
    )
    conn.execute("INSERT INTO dim_track VALUES (10, 'Hit', 1, 1, 80), (11, 'Miss', 1, 1, 40)")
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, nombre_artista VARCHAR,
            popularity INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_tracks_populares VALUES (10, 'Hit', 'Artist A', 80), (11, 'Miss', 'A', 40)")
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER, nombre_artista VARCHAR,
            streams_7d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_artist_growth VALUES (1, 'Artist A', 100, 25.0, 1000)")
    conn.execute(
        """
        CREATE TABLE agg_genre_trends (
            id_genero INTEGER, nombre_genero VARCHAR,
            streams_7d INTEGER, trend_pct DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_genre_trends VALUES (1, 'pop', 500, 15.0)")
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            streams INTEGER, skipped BOOLEAN, device_type VARCHAR, platform VARCHAR,
            fecha_evento TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO fact_streaming VALUES
        (1, 10, 1, 1, false, 'mobile', 'android', CURRENT_TIMESTAMP),
        (2, 10, 2, 1, false, 'mobile', 'android', CURRENT_TIMESTAMP),
        (3, 11, 2, 1, false, 'mobile', 'android', CURRENT_TIMESTAMP)
        """
    )
    conn.close()
    monkeypatch.setenv("DB_PATH", str(db_path))
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(db_path)
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield
    shutdown_duckdb_client()
    restore_session_db()


def test_popularity_min_max():
    assert score_popularity(50, min_pop=0, max_pop=100) == 0.5
    assert score_popularity(100, min_pop=0, max_pop=100, in_top_chart=True) >= 0.9


def test_engine_recommend(engine_db):
    engine = RecommendationEngine()
    recs = engine.recommend(1, limit=5)
    assert recs
    assert recs[0].score >= recs[-1].score
    assert 0 <= recs[0].score <= 1
    assert recs[0].reason


def test_trending_boost_scores():
    from app.db.duckdb_client import get_duckdb_client

    boost = TrendingBoost(get_duckdb_client())
    score = boost.score_track(artist_id=1, genre_id=1)
    assert 0 <= score <= 1
