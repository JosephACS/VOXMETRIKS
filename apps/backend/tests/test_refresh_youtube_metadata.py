"""Tests for YouTube metadata refresh — provider failure must not write."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from app.core.time_util import utc_now
from app.packages.streaming.services.audio.refresh_youtube_metadata import (
    refresh_youtube_metadata_batch,
)


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE app_track_audio_source (
            track_id INTEGER PRIMARY KEY,
            provider VARCHAR NOT NULL DEFAULT 'youtube',
            youtube_video_id VARCHAR,
            source_ref VARCHAR,
            playable_url VARCHAR,
            query VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'ok',
            failure_count INTEGER DEFAULT 0,
            confidence_score DOUBLE,
            resolved_at TIMESTAMP,
            last_checked_at TIMESTAMP
        )
        """
    )
    old = utc_now() - timedelta(days=60)
    conn.execute(
        """
        INSERT INTO app_track_audio_source
            (track_id, provider, youtube_video_id, source_ref, status,
             failure_count, query, resolved_at, last_checked_at)
        VALUES
          (1, 'youtube', 'vidAAAAAAA1', 'vidAAAAAAA1', 'ok', 2, 'q1', ?, ?),
          (2, 'youtube', 'vidAAAAAAA2', 'vidAAAAAAA2', 'ok', 0, 'q2', ?, ?)
        """,
        [old, old, old, old],
    )


def _snapshot(conn: duckdb.DuckDBPyConnection) -> list[tuple]:
    return conn.execute(
        """
        SELECT track_id, provider, youtube_video_id, source_ref, status,
               failure_count, query, resolved_at, last_checked_at, confidence_score
        FROM app_track_audio_source
        ORDER BY track_id
        """
    ).fetchall()


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    _seed(c)
    return c


@patch("app.packages.streaming.services.audio.refresh_youtube_metadata.YouTubeProvider")
@patch("app.packages.streaming.services.audio.refresh_youtube_metadata.get_settings")
def test_provider_none_is_provider_error_zero_writes(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = None
    before = _snapshot(conn)
    result = refresh_youtube_metadata_batch(conn, limit=10, max_age_days=30)
    after = _snapshot(conn)
    assert result["ok"] is False
    assert result["reason"] == "provider_error"
    assert result["processed"] == 0
    assert result.get("updated", 0) == 0
    assert result.get("removed", 0) == 0
    assert before == after


@patch("app.packages.streaming.services.audio.refresh_youtube_metadata.YouTubeProvider")
@patch("app.packages.streaming.services.audio.refresh_youtube_metadata.get_settings")
def test_absent_video_in_valid_dict_marks_not_found(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "vidAAAAAAA1": {
            "title": "Still Here",
            "channel_title": "Ch",
            "duration_sec": 200,
        }
        # vidAAAAAAA2 intentionally absent → not_found
    }
    result = refresh_youtube_metadata_batch(conn, limit=10, max_age_days=30)
    assert result["ok"] is True
    assert result["updated"] == 1
    assert result["removed"] == 1
    row2 = conn.execute(
        "SELECT status FROM app_track_audio_source WHERE track_id = 2"
    ).fetchone()
    assert row2[0] == "not_found"
    row1 = conn.execute(
        "SELECT status FROM app_track_audio_source WHERE track_id = 1"
    ).fetchone()
    assert row1[0] == "ok"
