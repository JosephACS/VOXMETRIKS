"""Dashboard API and cache tests."""

from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.cache import cache_invalidate
from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.etl.gold.dashboard_cache import build_agg_dashboard_cache
from app.services.dashboard_service import DashboardService


@pytest.fixture()
def dash_db(tmp_path, monkeypatch):
    db_path = tmp_path / "dash.duckdb"
    conn = duckdb.connect(str(db_path))

    conn.execute("CREATE TABLE dim_track (id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, popularity INTEGER)")
    conn.execute("INSERT INTO dim_track SELECT i, 'Track ' || i, 50 FROM generate_series(1, 5) g(i)")
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
        ('2026-06-01', 100, 10, 5, 180000.0, 31.0),
        ('2026-06-08', 150, 15, 6, 200000.0, 28.0)
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
    conn.execute("INSERT INTO agg_genero_popularidad VALUES (1, 'reggaeton', 80.0, 0.7, 100, 20)")
    conn.execute(
        """
        CREATE TABLE agg_user_engagement (
            segment VARCHAR PRIMARY KEY, user_count INTEGER,
            avg_plays DOUBLE, avg_session_min DOUBLE, retention_pct DOUBLE
        )
        """
    )
    conn.execute(
        """
        INSERT INTO agg_user_engagement VALUES
        ('power_users', 2, 50.0, 22.5, 75.0),
        ('regular_users', 5, 20.0, 15.0, 50.0),
        ('casual_users', 10, 5.0, 8.0, 25.0)
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
    conn.execute("INSERT INTO agg_tracks_populares VALUES (1, 'Hit', 'Artist', 90, 500, 800.0)")
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR,
            streams_7d INTEGER, streams_30d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_artist_growth VALUES (1, 'Top Artist', 1000, 4000, 15.5, 5000)")
    conn.execute(
        """
        CREATE TABLE agg_platform_usage (
            platform VARCHAR, device_type VARCHAR, session_count INTEGER,
            total_streams INTEGER, avg_session_min DOUBLE, share_pct DOUBLE,
            PRIMARY KEY (platform, device_type)
        )
        """
    )
    conn.execute("INSERT INTO agg_platform_usage VALUES ('android', 'mobile', 10, 100, 22.0, 60.0)")

    build_agg_dashboard_cache(conn)
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    get_settings.cache_clear()
    shutdown_duckdb_client()
    cache_invalidate()
    from app.core.database import close_read_pool, open_read_pool

    close_read_pool()
    yield db_path
    shutdown_duckdb_client()
    close_read_pool()
    get_settings.cache_clear()
    try:
        open_read_pool(get_settings().db_path_resolved)
    except Exception:
        pass


def test_dashboard_overview(dash_db):
    service = DashboardService()
    overview = service.get_overview()
    assert overview.total_streams == 150
    assert overview.top_genre == "reggaeton"
    assert overview.skip_rate == pytest.approx(0.28, abs=0.01)


def test_dashboard_engagement(dash_db):
    service = DashboardService()
    eng = service.get_engagement()
    assert len(eng.segments) == 3
    assert eng.power_users_pct > 0


def test_dashboard_api_routes(dash_db):
    from app.main import app
    from app.packages.identity.services.auth_deps import require_user_id
    from app.core.schema_bootstrap import mark_schema_ready, reset_schema_ready_for_tests, schema_ready

    was_ready = schema_ready()
    reset_schema_ready_for_tests()
    app.dependency_overrides[require_user_id] = lambda: 1
    try:
        with TestClient(app) as client:
            resp = client.get("/api/v2/dashboard/overview")
            assert resp.status_code == 200
            assert resp.json()["total_streams"] == 150
            assert "X-Response-Time-Ms" in resp.headers

            growth = client.get("/api/v2/dashboard/growth")
            assert growth.status_code == 200
            assert "weekly_growth_pct" in growth.json()
    finally:
        app.dependency_overrides.pop(require_user_id, None)
        if was_ready:
            mark_schema_ready()
        else:
            reset_schema_ready_for_tests()
