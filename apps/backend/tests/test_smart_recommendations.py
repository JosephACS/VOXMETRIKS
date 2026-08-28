"""Tests for Smart Recommendation Engine — Phase 4."""

from unittest.mock import patch

import duckdb
import pytest

from app.packages.analytics.services.smart.discover_weekly import build_discover_weekly
from app.packages.analytics.services.smart.feature_extractor import (
    audio_dna_profile,
    track_vector,
)
from app.packages.analytics.services.smart.home_composer import compose_home
from app.packages.analytics.services.smart.similarity_engine import (
    cosine_similarity,
    similar_tracks,
)
from app.packages.analytics.services.smart.spotify_taste import rank_from_spotify_taste

_MOCK_RANK = [
    {
        "id_track": 1,
        "nombre_track": "Track A",
        "nombre_artista": "Artist A",
        "score": 0.9,
        "reason": "high_popularity",
        "popularity": 80,
    },
    {
        "id_track": 2,
        "nombre_track": "Track B",
        "nombre_artista": "Artist B",
        "score": 0.8,
        "reason": "catalog_discovery",
        "popularity": 70,
    },
]


@pytest.fixture
def smart_conn():
    c = duckdb.connect(":memory:")
    c.execute("CREATE TABLE dim_genero (id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR)")
    c.execute("INSERT INTO dim_genero VALUES (1, 'pop')")
    c.execute("CREATE TABLE dim_artista (id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR)")
    c.execute("INSERT INTO dim_artista VALUES (1, 'Artist A'), (2, 'Artist B')")
    c.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR, nombre_track VARCHAR,
            id_artista INTEGER, id_genero INTEGER, popularity INTEGER,
            danceability DOUBLE, energy DOUBLE, speechiness DOUBLE,
            acousticness DOUBLE, instrumentalness DOUBLE, liveness DOUBLE,
            valence DOUBLE, tempo DOUBLE
        )
        """
    )
    c.execute(
        """
        INSERT INTO dim_track VALUES
        (1, 'sp_track_a', 'Track A', 1, 1, 80, 0.8, 0.9, 0.05, 0.1, 0.0, 0.1, 0.7, 120),
        (2, 'sp_track_b', 'Track B', 2, 1, 70, 0.79, 0.88, 0.06, 0.12, 0.0, 0.12, 0.68, 118),
        (3, 'sp_track_c', 'Track C', 2, 1, 40, 0.05, 0.05, 0.9, 0.95, 0.9, 0.9, 0.05, 60)
        """
    )
    c.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR,
            nombre_artista VARCHAR, popularity INTEGER
        )
        """
    )
    c.execute(
        "INSERT INTO agg_tracks_populares VALUES (1, 'Track A', 'Artist A', 80), (2, 'Track B', 'Artist B', 70), (3, 'Track C', 'Artist B', 40)"
    )
    c.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            streams INTEGER, skipped BOOLEAN, fecha_evento TIMESTAMP
        )
        """
    )
    c.execute(
        "INSERT INTO fact_streaming VALUES (1, 1, 1, 1, false, CURRENT_TIMESTAMP)"
    )
    c.execute(
        """
        CREATE TABLE app_favorite (user_id INTEGER, track_id INTEGER, added_at TIMESTAMP,
            PRIMARY KEY (user_id, track_id))
        """
    )
    c.execute("INSERT INTO app_favorite VALUES (1, 1, CURRENT_TIMESTAMP)")
    return c


def test_cosine_similarity_identical():
    v = track_vector({"energy": 0.8, "danceability": 0.7, "valence": 0.6, "tempo": 120})
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=0.01)


def test_similar_tracks_finds_neighbor(smart_conn):
    similar = similar_tracks(smart_conn, 1, limit=5)
    ids = [t["id_track"] for t in similar]
    assert 2 in ids
    assert 3 not in ids


def test_audio_dna_profile():
    vec = track_vector({"energy": 0.85, "danceability": 0.7, "acousticness": 0.1, "instrumentalness": 0.05, "valence": 0.6, "tempo": 120})
    dna = audio_dna_profile(vec)
    assert dna["energetic"] >= 80
    assert dna["dance"] >= 60


def test_discover_weekly_has_tracks(smart_conn):
    with patch(
        "app.packages.analytics.services.smart.discover_weekly.RankingEngine.rank_for_user",
        return_value=_MOCK_RANK,
    ):
        weekly = build_discover_weekly(smart_conn, 1, limit=5)
    assert weekly["code"] == "discover_weekly"
    assert "title" not in weekly or weekly.get("title") != "Discover Weekly"
    assert len(weekly["tracks"]) >= 1


def test_home_compose_sections(smart_conn):
    with patch(
        "app.packages.analytics.services.smart.home_composer.RankingEngine.rank_for_user",
        return_value=_MOCK_RANK,
    ):
        home = compose_home(smart_conn, 1)
    assert home["user_id"] == 1
    assert isinstance(home["sections"], list)
    assert home["profile"]["audio_dna"] is not None


def test_spotify_taste_reranks_and_reports_catalog_coverage(smart_conn):
    with patch(
        "app.packages.analytics.services.smart.spotify_taste.RankingEngine.rank_for_user",
        return_value=[_MOCK_RANK[1], _MOCK_RANK[0]],
    ):
        result = rank_from_spotify_taste(
            smart_conn,
            app_user_id=1,
            warehouse_user_id=1,
            top_track_ids=["sp_track_a"],
            recent_track_ids=["missing_from_catalog"],
            saved_track_ids=[],
            limit=2,
        )

    assert result["source"] == "spotify_taste_vox"
    assert result["coverage"] == {
        "spotify_signals": 2,
        "matched_catalog_tracks": 1,
        "match_percent": 50.0,
    }
    assert len(result["tracks"]) == 1
    assert result["tracks"][0]["spotify_uri"] == "spotify:track:sp_track_b"
    assert result["tracks"][0]["source"] == "spotify_taste_vox"
