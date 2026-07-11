"""Tests for V2 enterprise API (/api/v2)."""

from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture()
def api_v2_db(tmp_path, monkeypatch):
    db_path = tmp_path / "api_v2.duckdb"
    conn = duckdb.connect(str(db_path))

    conn.execute(
        """
        CREATE TABLE dim_genero (id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR)
        """
    )
    conn.execute("INSERT INTO dim_genero VALUES (1, 'pop'), (2, 'rock')")
    conn.execute(
        "CREATE TABLE dim_artista (id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR)"
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist A'), (2, 'Artist B')")
    conn.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR, nombre_track VARCHAR,
            id_artista INTEGER, id_genero INTEGER, popularity INTEGER, energy DOUBLE
        )
        """
    )
    conn.execute(
        """
        INSERT INTO dim_track VALUES
        (1, 't1', 'Track One', 1, 1, 80, 0.8),
        (2, 't2', 'Track Two', 2, 2, 60, 0.5)
        """
    )
    conn.execute(
        """
        CREATE TABLE dim_usuario (
            id_usuario INTEGER PRIMARY KEY, nombre VARCHAR, email VARCHAR,
            pais VARCHAR, plan VARCHAR, fecha_registro TIMESTAMP
        )
        """
    )
    conn.execute(
        "INSERT INTO dim_usuario VALUES (1, 'Alice', 'a@test.com', 'CO', 'premium', now())"
    )
    conn.execute(
        """
        CREATE TABLE dim_playlist (id_playlist INTEGER PRIMARY KEY, nombre_playlist VARCHAR)
        """
    )
    conn.execute("INSERT INTO dim_playlist VALUES (1, 'Chill Pop Mix')")
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            id_playlist INTEGER, streams INTEGER, duracion_ms INTEGER,
            completado BOOLEAN, fecha_evento TIMESTAMP, skipped BOOLEAN,
            device_type VARCHAR, platform VARCHAR, session_id INTEGER,
            hour_of_day INTEGER, engagement_score DOUBLE
        )
        """
    )
    conn.execute(
        """
        INSERT INTO fact_streaming VALUES
        (1, 1, 1, NULL, 2, 180000, true, '2026-06-01 10:00:00', false, 'mobile', 'web', 100, 10, 360.0),
        (2, 1, 1, NULL, 1, 90000, false, '2026-06-01 11:00:00', true, 'mobile', 'web', 100, 11, 90.0)
        """
    )
    conn.execute(
        """
        CREATE TABLE agg_daily_streams (
            fecha DATE PRIMARY KEY, total_streams INTEGER, unique_users INTEGER,
            unique_tracks INTEGER, avg_duration_ms DOUBLE, skip_rate DOUBLE
        )
        """
    )
    conn.execute(
        """
        INSERT INTO agg_daily_streams VALUES
        ('2026-06-01', 2, 1, 1, 135000.0, 50.0)
        """
    )
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR, streams_7d INTEGER,
            streams_30d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO agg_artist_growth VALUES (1, 'Artist A', 100, 400, 12.5, 500)"
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
        (1, 'Track One', 'Artist A', 80, 100, 360.0)
        """
    )
    conn.execute(
        """
        CREATE TABLE agg_genero_popularidad (
            id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR,
            popularidad_promedio DOUBLE, energia_promedio DOUBLE,
            total_tracks INTEGER, total_artistas INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO agg_genero_popularidad VALUES (1, 'pop', 75.0, 0.7, 1, 1)"
    )
    conn.execute(
        """
        CREATE TABLE agg_platform_usage (
            platform VARCHAR, device_type VARCHAR, session_count INTEGER,
            total_streams INTEGER, avg_session_min DOUBLE, share_pct DOUBLE,
            PRIMARY KEY (platform, device_type)
        )
        """
    )
    conn.execute(
        "INSERT INTO agg_platform_usage VALUES ('web', 'mobile', 1, 2, 7.0, 100.0)"
    )
    conn.execute(
        """
        CREATE TABLE agg_user_engagement (
            segment VARCHAR PRIMARY KEY, user_count INTEGER, avg_plays DOUBLE,
            avg_session_min DOUBLE, retention_pct DOUBLE
        )
        """
    )
    conn.execute(
        "INSERT INTO agg_user_engagement VALUES ('power_users', 1, 2.0, 6.4, 75.0)"
    )
    conn.close()

    from app.etl.gold.dashboard_cache import build_agg_dashboard_cache

    conn2 = duckdb.connect(str(db_path))
    build_agg_dashboard_cache(conn2)
    conn2.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    get_settings.cache_clear()

    from app.db.duckdb_client import shutdown_duckdb_client

    shutdown_duckdb_client()
    yield db_path
    shutdown_duckdb_client()
    get_settings.cache_clear()


@pytest.fixture()
def v2_client(api_v2_db):
    from app.main import app
    from app.packages.identity.services.auth_deps import require_user_id

    # Isolated warehouse has no app_user (schema_ready already true from session client).
    app.dependency_overrides[require_user_id] = lambda: 1
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(require_user_id, None)


def test_analytics_daily_streams(v2_client):
    resp = v2_client.get("/api/v2/analytics/daily-streams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_streams"] == 2
    assert body["skip_rate"] == 0.5


def test_analytics_top_artists(v2_client):
    resp = v2_client.get("/api/v2/analytics/top-artists")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_user_profile_and_activity(v2_client):
    profile = v2_client.get("/api/v2/users/1")
    assert profile.status_code == 200
    assert profile.json()["nombre"] == "Alice"

    activity = v2_client.get("/api/v2/users/1/activity")
    assert activity.status_code == 200
    assert activity.json()["plays"] == 2


def test_search(v2_client):
    resp = v2_client.get("/api/v2/search", params={"q": "Track"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tracks"]) >= 1


def test_recommendations(v2_client):
    resp = v2_client.get("/api/v2/recommendations/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert "recommendations" in body
    assert body["recommendations"][0]["score"] >= 0
    assert body["recommendations"][0]["reason"]


def test_stream_lifecycle(v2_client):
    start = v2_client.post(
        "/api/v2/stream/start",
        json={"user_id": 1, "track_id": 1, "device_type": "mobile", "platform": "android"},
    )
    assert start.status_code == 201
    body = start.json()
    stream_id = body["stream_id"]
    session_id = body["session_id"]
    assert body["event_type"] == "STREAM_START"
    assert session_id >= 1

    pause = v2_client.post(
        "/api/v2/stream/pause",
        json={"stream_id": stream_id, "duration_ms": 60000},
    )
    assert pause.status_code == 200
    assert pause.json()["event_type"] == "STREAM_PAUSE"

    resume = v2_client.post(
        "/api/v2/stream/resume",
        json={"stream_id": stream_id},
    )
    assert resume.status_code == 200
    assert resume.json()["event_type"] == "STREAM_RESUME"

    end = v2_client.post(
        "/api/v2/stream/end",
        json={"stream_id": stream_id, "duration_ms": 120000, "completed": True, "skipped": False},
    )
    assert end.status_code == 200
    end_body = end.json()
    assert end_body["duration_ms"] == 120000
    assert end_body["session_id"] == session_id
    assert end_body["engagement_score"] > 0

    live = v2_client.get("/api/v2/stream/session/1/live")
    assert live.status_code == 200
    live_body = live.json()
    assert live_body["tracks_played"] >= 1


def test_stream_skip(v2_client):
    start = v2_client.post(
        "/api/v2/stream/start",
        json={"user_id": 1, "track_id": 1, "device_type": "mobile", "platform": "android"},
    )
    stream_id = start.json()["stream_id"]
    skip = v2_client.post(
        "/api/v2/stream/skip",
        json={"stream_id": stream_id, "duration_ms": 15000},
    )
    assert skip.status_code == 200
    assert skip.json()["event_type"] == "STREAM_SKIP"
    assert skip.json()["engagement_score"] is not None
