"""Regression: dashboard/analytics tolerate warehouse agg_tracks_populares without engagement_score."""

from __future__ import annotations

import duckdb
import pytest

from app.core.cache import cache_invalidate
from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.pipeline.orchestrator import _warm_cache
from app.services.analytics_service import AnalyticsService
from app.services.dashboard_service import DashboardService


@pytest.fixture()
def warehouse_style_agg(tmp_path, monkeypatch):
    """Schema matching analytics/elt warehouse (no engagement_score / total_streams)."""
    db_path = tmp_path / "wh_style.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY,
            nombre_track VARCHAR,
            nombre_artista VARCHAR,
            nombre_album VARCHAR,
            nombre_genero VARCHAR,
            popularity INTEGER,
            energy DOUBLE,
            danceability DOUBLE,
            valence DOUBLE,
            tempo DOUBLE,
            duration_ms INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO agg_tracks_populares VALUES
        (1, 'Song A', 'Artist A', 'Album', 'pop', 90, 0.5, 0.6, 0.4, 120.0, 200000),
        (2, 'Song B', 'Artist B', 'Album', 'rock', 70, 0.7, 0.5, 0.3, 110.0, 180000)
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
        """
        INSERT INTO agg_user_engagement VALUES
        ('power_users', 2, 50.0, 22.5, 75.0),
        ('regular_users', 5, 20.0, 15.0, 50.0)
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
        "INSERT INTO agg_daily_streams VALUES ('2026-07-01', 100, 10, 5, 180000.0, 0.2)"
    )
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    get_settings.cache_clear()
    shutdown_duckdb_client()
    cache_invalidate()
    yield db_path
    shutdown_duckdb_client()
    get_settings.cache_clear()


def test_engagement_without_engagement_score_column(warehouse_style_agg):
    eng = DashboardService().get_engagement()
    assert len(eng.segments) == 2
    # Must not invent a score from agg_tracks_populares; segment avg_plays is the fallback source.
    assert eng.avg_engagement_score == pytest.approx(35.0, abs=0.01)


def test_live_tracks_omit_missing_metrics(warehouse_style_agg):
    tracks = DashboardService()._top_live_tracks(limit=5)
    assert len(tracks) == 2
    assert tracks[0].track_id == 1
    assert tracks[0].streams is None
    assert tracks[0].engagement_score is None


def test_analytics_top_tracks_null_engagement(warehouse_style_agg):
    result = AnalyticsService().get_top_tracks(limit=5)
    assert result.count == 2
    assert result.items[0].engagement_score is None
    assert result.items[0].total_streams is None
    assert result.items[0].popularity == 90


def test_warm_cache_tolerates_missing_engagement_score(warehouse_style_agg):
    _warm_cache()  # must not raise


def test_warm_cache_rethrows_unexpected_errors(warehouse_style_agg, monkeypatch):
    def boom():
        raise RuntimeError("critical-failure")

    monkeypatch.setattr(
        "app.services.dashboard_service.DashboardService.get_overview",
        lambda self: boom(),
    )
    with pytest.raises(RuntimeError, match="critical-failure"):
        _warm_cache()
