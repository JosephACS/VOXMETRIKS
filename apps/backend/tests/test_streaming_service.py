"""Tests for event-driven streaming service."""

from __future__ import annotations

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.models.schemas import StreamActionRequest, StreamEndRequest, StreamStartRequest
from app.services.streaming_service import EVENT_END, EVENT_SKIP, EVENT_START, StreamingService


@pytest.fixture()
def stream_db(tmp_path, monkeypatch):
    db_path = tmp_path / "stream_events.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR,
            duration_ms INTEGER, popularity INTEGER
        )
        """
    )
    conn.execute("INSERT INTO dim_track VALUES (1, 'Test Track', 180000, 80)")
    conn.execute(
        """
        CREATE TABLE fact_streaming (
            id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER,
            streams INTEGER, duracion_ms INTEGER, completado BOOLEAN,
            skipped BOOLEAN, device_type VARCHAR, platform VARCHAR,
            session_id INTEGER, fecha_evento TIMESTAMP, hour_of_day INTEGER,
            engagement_score DOUBLE
        )
        """
    )
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield db_path
    shutdown_duckdb_client()
    get_settings.cache_clear()


def test_stream_events_write_facts(stream_db):
    service = StreamingService()
    start = service.start_stream(
        StreamStartRequest(user_id=1, track_id=1, device_type="mobile", platform="android")
    )
    assert start.event_type == EVENT_START
    assert start.session_id >= 1

    end = service.end_stream(
        StreamEndRequest(stream_id=start.stream_id, duration_ms=170000, completed=True)
    )
    assert end.event_type == EVENT_END
    assert end.engagement_score > 0.5

    stats = service.get_live_session_stats(1)
    assert stats.active is True
    assert stats.tracks_played >= 1


def test_skip_penalizes_engagement(stream_db):
    service = StreamingService()
    start = service.start_stream(
        StreamStartRequest(user_id=2, track_id=1, device_type="desktop", platform="web")
    )
    skip = service.skip_track(
        StreamActionRequest(stream_id=start.stream_id, duration_ms=5000)
    )
    assert skip.event_type == EVENT_SKIP
    assert skip.engagement_score is not None
    assert skip.engagement_score < 0.3
