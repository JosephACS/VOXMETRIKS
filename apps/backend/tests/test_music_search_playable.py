"""Unit tests for playable filter and unified music search (YouTube mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from app.packages.catalog.services.music_search_service import adopt_youtube_result, music_search
from app.packages.catalog.services.tracks.list import get_tracks
from app.packages.catalog.services.tracks.playback_availability import (
    PLAYABLE,
    playable_track_sql,
    playback_status_for_cache,
)


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE dim_artista (id_artista INTEGER, nombre_artista VARCHAR);
        CREATE TABLE dim_genero (id_genero INTEGER, nombre_genero VARCHAR);
        CREATE TABLE dim_track (
          id_track INTEGER,
          spotify_track_id VARCHAR,
          nombre_track VARCHAR,
          id_artista INTEGER,
          id_album INTEGER,
          id_genero INTEGER,
          explicit BOOLEAN,
          duration_ms INTEGER,
          popularity INTEGER
        );
        CREATE TABLE app_track_audio_source (
          track_id INTEGER,
          provider VARCHAR,
          status VARCHAR,
          failure_count INTEGER,
          youtube_video_id VARCHAR,
          source_ref VARCHAR,
          playable_url VARCHAR
        );
        """
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'The Weeknd'), (2, 'Other')")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'Pop')")
    conn.execute(
        """
        INSERT INTO dim_track VALUES
          (10, 'sp10', 'Blinding Lights', 1, NULL, 1, false, 200000, 90),
          (11, 'sp11', 'Save Your Tears', 1, NULL, 1, false, 210000, 80),
          (12, 'sp12', 'Ghost Song', 2, NULL, 1, false, 180000, 10)
        """
    )
    conn.execute(
        """
        INSERT INTO app_track_audio_source VALUES
          (10, 'youtube', 'ok', 0, 'dQw4w9WgXcQ', 'dQw4w9WgXcQ', NULL),
          (11, 'youtube', 'error', 5, 'aaaaaaaaaaa', 'aaaaaaaaaaa', NULL)
        """
    )


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    _seed(c)
    return c


def test_playable_sql_requires_ok_source(conn: duckdb.DuckDBPyConnection) -> None:
    pred = playable_track_sql(conn)
    rows = conn.execute(
        f"SELECT id_track FROM dim_track dt WHERE {pred} ORDER BY id_track"
    ).fetchall()
    assert [r[0] for r in rows] == [10]


def test_list_playable_only_default(conn: duckdb.DuckDBPyConnection) -> None:
    items, total = get_tracks(conn, page=1, limit=50, playable_only=True)
    assert total == 1
    assert items[0]["id_track"] == 10


def test_list_all_when_playable_false(conn: duckdb.DuckDBPyConnection) -> None:
    items, total = get_tracks(conn, page=1, limit=50, playable_only=False)
    assert total == 3
    assert len(items) == 3


def test_playback_status_mapping() -> None:
    assert playback_status_for_cache(None) == "missing"
    assert playback_status_for_cache({"status": "ok", "failure_count": 0}) == PLAYABLE
    assert playback_status_for_cache({"status": "error", "failure_count": 5}) == "failed"


def test_music_search_local_playable(conn: duckdb.DuckDBPyConnection) -> None:
    out = music_search(conn, "Blinding Lights", allow_external=True)
    assert out["phase"] == "local"
    assert out["local"]["total"] >= 1
    assert out["external"] == []


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_music_search_external_fallback(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value.search_query_candidates.return_value = [
        {
            "video_id": "bbbbbbbbbbb",
            "title": "Unknown Hit",
            "channel_title": "Channel",
            "duration_sec": 200,
            "thumbnail": "https://i.ytimg.com/vi/bbbbbbbbbbb/hqdefault.jpg",
            "origin": "youtube",
        }
    ]
    out = music_search(conn, "Unknown Hit XYZ", allow_external=True)
    assert out["phase"] == "external"
    assert len(out["external"]) == 1
    assert out["external"][0]["video_id"] == "bbbbbbbbbbb"
    mock_yt.return_value.search_query_candidates.assert_called_once()


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_music_search_skips_youtube_when_local(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    music_search(conn, "Blinding", allow_external=True)
    mock_yt.return_value.search_query_candidates.assert_not_called()


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_attaches_to_existing_missing_track(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "ccccccccccc": {
            "title": "Ghost Song",
            "channel_title": "Other",
            "duration_sec": 180,
            "thumbnail": "",
        }
    }
    out = adopt_youtube_result(conn, video_id="ccccccccccc", preferred_track_id=12)
    assert out["track_id"] == 12
    assert out["created"] is False
    mock_yt.return_value._fetch_video_details.assert_called_once()
    row = conn.execute(
        "SELECT track_id FROM app_track_audio_source WHERE youtube_video_id = 'ccccccccccc'"
    ).fetchone()
    assert row is not None and int(row[0]) == 12


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_reuses_existing_video_id(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    out = adopt_youtube_result(conn, video_id="dQw4w9WgXcQ")
    assert out["track_id"] == 10
    assert out["reused_source"] is True
    mock_yt.return_value._fetch_video_details.assert_not_called()
