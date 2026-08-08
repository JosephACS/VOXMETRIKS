"""Adopt integrity: atomicity, repair placement, rate limit, YouTube contract."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import duckdb
import pytest
from pydantic import ValidationError

from app.packages.catalog.services.music_search_service import (
    AdoptRateLimitError,
    TrackSourceMismatchError,
    adopt_youtube_result,
    clear_adopt_rate_limit_buckets,
    repair_youtube_source_association,
    reserve_adopt_validation_quota,
)
from app.packages.catalog.services.track_source_match import (
    build_identity_from_track,
    build_identity_from_youtube,
    is_incompatible,
    is_strong_match,
    versions_compatible,
)
from app.shared.schemas.models import MusicSearchAdoptRequest


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
          track_id INTEGER PRIMARY KEY,
          provider VARCHAR,
          status VARCHAR,
          failure_count INTEGER,
          youtube_video_id VARCHAR,
          source_ref VARCHAR,
          playable_url VARCHAR,
          query VARCHAR,
          confidence_score DOUBLE,
          resolved_at TIMESTAMP,
          last_checked_at TIMESTAMP
        );
        """
    )
    conn.execute(
        "INSERT INTO dim_artista VALUES (1, 'Alan Walker;Benjamin Ingrosso'), (2, 'The Weeknd'), (3, 'Other')"
    )
    conn.execute("INSERT INTO dim_genero VALUES (1, 'Pop')")
    conn.execute(
        """
        INSERT INTO dim_track VALUES
          (10, 'sp10', 'Blinding Lights', 2, NULL, 1, false, 200000, 90),
          (11, 'sp11', 'Blinding Lights (Remix)', 2, NULL, 1, false, 210000, 70),
          (12, 'sp12', 'Ghost Song', 3, NULL, 1, false, 180000, 10),
          (13, 'sp13', 'Man On The Moon', 1, NULL, 1, false, 178625, 73)
        """
    )
    conn.execute(
        """
        INSERT INTO app_track_audio_source
          (track_id, provider, status, failure_count, youtube_video_id, source_ref)
        VALUES (10, 'youtube', 'ok', 0, 'dQw4w9WgXcQ', 'dQw4w9WgXcQ')
        """
    )


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    _seed(c)
    return c


@pytest.fixture(autouse=True)
def _clear_quota():
    clear_adopt_rate_limit_buckets()
    yield
    clear_adopt_rate_limit_buckets()


def test_same_title_different_artist_not_merged() -> None:
    track = build_identity_from_track(title="Blinding Lights", artist="Revelries;Victoria Voss")
    src = build_identity_from_youtube(
        title="The Weeknd - Blinding Lights",
        channel_title="David Dean Burkhart",
    )
    assert is_incompatible(track, src)
    assert not is_strong_match(track, src)


def test_match_same_song() -> None:
    track = build_identity_from_track(title="Man On The Moon", artist="Alan Walker")
    src = build_identity_from_youtube(
        title="Alan Walker - Man On The Moon (Official Audio)",
        channel_title="Alan Walker",
    )
    assert is_strong_match(track, src)
    assert not is_incompatible(track, src)


def test_mismatch_different_songs() -> None:
    track = build_identity_from_track(title="Man On The Moon", artist="Alan Walker")
    src = build_identity_from_youtube(
        title="The Weeknd - Blinding Lights",
        channel_title="The Weeknd",
    )
    assert is_incompatible(track, src)
    assert not is_strong_match(track, src)


def test_remix_not_merged_with_original() -> None:
    original = build_identity_from_track(title="Blinding Lights", artist="The Weeknd")
    remix = build_identity_from_youtube(
        title="The Weeknd - Blinding Lights (Remix)",
        channel_title="The Weeknd",
    )
    assert not versions_compatible(set(original.version_markers), set(remix.version_markers))
    assert not is_strong_match(original, remix)


def test_live_and_cover_not_auto_merged() -> None:
    original = build_identity_from_track(title="Blinding Lights", artist="The Weeknd")
    live = build_identity_from_youtube(title="Blinding Lights Live", channel_title="The Weeknd")
    cover = build_identity_from_youtube(title="Blinding Lights Cover", channel_title="Someone")
    assert not is_strong_match(original, live)
    assert not is_strong_match(original, cover)


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_compatible_missing_track(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "moonmoonmoo": {
            "title": "Alan Walker - Man On The Moon",
            "channel_title": "Alan Walker",
            "duration_sec": 179,
            "thumbnail": "",
        }
    }
    out = adopt_youtube_result(conn, video_id="moonmoonmoo", preferred_track_id=13)
    assert out["track_id"] == 13
    assert out["created"] is False
    assert out.get("preferred_rejected") is False
    mock_yt.return_value._fetch_video_details.assert_called_once()
    row = conn.execute(
        "SELECT track_id FROM app_track_audio_source WHERE youtube_video_id = 'moonmoonmoo'"
    ).fetchone()
    assert row is not None and int(row[0]) == 13


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_rejects_incompatible_preferred(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "blindsblind": {
            "title": "The Weeknd - Blinding Lights",
            "channel_title": "The Weeknd",
            "duration_sec": 200,
            "thumbnail": "",
        }
    }
    with pytest.raises(TrackSourceMismatchError):
        adopt_youtube_result(
            conn,
            video_id="blindsblind",
            preferred_track_id=13,
            require_preferred=True,
        )
    out = adopt_youtube_result(conn, video_id="blindsblind", preferred_track_id=13)
    assert out["track_id"] != 13
    assert out["preferred_rejected"] is True
    assert out["track_id"] == 10


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_creates_new_when_no_compatible(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "newnewsongg": {
            "title": "Brand New Indie Hit - Unique Song XYZ",
            "channel_title": "Indie Channel",
            "duration_sec": 210,
            "thumbnail": "",
        }
    }
    out = adopt_youtube_result(conn, video_id="newnewsongg")
    assert out["created"] is True
    assert out["track_id"] not in {10, 11, 12, 13}
    row = conn.execute(
        "SELECT track_id FROM app_track_audio_source WHERE youtube_video_id = 'newnewsongg'"
    ).fetchone()
    assert row is not None and int(row[0]) == out["track_id"]


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_repair_moves_mismatched_source(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    conn.execute(
        """
        INSERT INTO app_track_audio_source
          (track_id, provider, status, failure_count, youtube_video_id, source_ref)
        VALUES (13, 'youtube', 'ok', 0, '8E0GXu9d0tk', '8E0GXu9d0tk')
        """
    )
    mock_yt.return_value._fetch_video_details.return_value = {
        "8E0GXu9d0tk": {
            "title": "The Weeknd - Blinding Lights",
            "channel_title": "The Weeknd",
            "duration_sec": 200,
            "thumbnail": "",
        }
    }
    # Track 10 already has another video; repair must overwrite onto the correct track.
    result = repair_youtube_source_association(conn, video_id="8E0GXu9d0tk")
    assert result["action"] == "reassigned"
    assert result["previous_track_id"] == 13
    assert result["track_id"] == 10
    assert not conn.execute(
        "SELECT 1 FROM app_track_audio_source WHERE track_id = 13 AND youtube_video_id = '8E0GXu9d0tk'"
    ).fetchone()
    row = conn.execute(
        "SELECT track_id FROM app_track_audio_source WHERE youtube_video_id = '8E0GXu9d0tk'"
    ).fetchone()
    assert row is not None
    assert int(row[0]) == 10


@patch("app.packages.catalog.services.music_search_service._persist_source")
@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_persistence_failure_full_rollback(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    mock_persist: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "rollbackvid": {
            "title": "Brand New Rollback Song UniqueZZZ",
            "channel_title": "Rollback Channel",
            "duration_sec": 200,
            "thumbnail": "",
        }
    }
    mock_persist.side_effect = RuntimeError("persist boom")
    tracks_before = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    artists_before = conn.execute("SELECT COUNT(*) FROM dim_artista").fetchone()[0]
    with pytest.raises(RuntimeError):
        adopt_youtube_result(conn, video_id="rollbackvid")
    assert conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0] == tracks_before
    assert conn.execute("SELECT COUNT(*) FROM dim_artista").fetchone()[0] == artists_before
    assert not conn.execute(
        "SELECT 1 FROM app_track_audio_source WHERE youtube_video_id = 'rollbackvid'"
    ).fetchone()


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_single_fetch_no_double_validate(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"
    mock_yt.return_value._fetch_video_details.return_value = {
        "onceonceonc": {
            "title": "Ghost Song",
            "channel_title": "Other",
            "duration_sec": 180,
            "thumbnail": "",
        }
    }
    adopt_youtube_result(conn, video_id="onceonceonc", preferred_track_id=12)
    assert mock_yt.return_value._fetch_video_details.call_count == 1


def test_reuse_does_not_consume_quota(conn: duckdb.DuckDBPyConnection) -> None:
    for _ in range(25):
        out = adopt_youtube_result(conn, video_id="dQw4w9WgXcQ", user_id=7)
        assert out["reused_source"] is True
    # Still able to reserve after many reuses
    reserve_adopt_validation_quota(7)


@patch("app.packages.catalog.services.music_search_service.YouTubeProvider")
@patch("app.packages.catalog.services.music_search_service.get_settings")
def test_adopt_rate_limit_user(
    mock_settings: MagicMock,
    mock_yt: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    mock_settings.return_value.youtube_api_key = "test-key"

    def _details(ids, _key):
        vid = ids[0]
        return {
            vid: {
                "title": f"Unique Song {vid}",
                "channel_title": "Channel",
                "duration_sec": 200,
                "thumbnail": "",
            }
        }

    mock_yt.return_value._fetch_video_details.side_effect = _details
    # 20 new validations OK
    for i in range(20):
        vid = f"rate{i:07d}"  # 11 chars
        adopt_youtube_result(conn, video_id=vid, user_id=42)
    with pytest.raises(AdoptRateLimitError):
        adopt_youtube_result(conn, video_id="rateOVERFLO", user_id=42)


def test_adopt_request_model_rejects_bad_types() -> None:
    with pytest.raises(ValidationError):
        MusicSearchAdoptRequest(video_id="short")
    with pytest.raises(ValidationError):
        MusicSearchAdoptRequest(video_id="dQw4w9WgXcQ", track_id="12")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        MusicSearchAdoptRequest(video_id="dQw4w9WgXcQ", require_preferred="yes")  # type: ignore[arg-type]
    ok = MusicSearchAdoptRequest(video_id="dQw4w9WgXcQ", track_id=10, require_preferred=True)
    assert ok.track_id == 10


@patch("app.packages.catalog.services.music_search_service._fetch_youtube_meta")
def test_concurrent_adopt_same_video_one_association(
    mock_fetch: MagicMock,
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Two threads adopting the same new videoId → one source, no duplicate tracks."""
    barrier = threading.Barrier(2)
    meta = {
        "title": "Concurrent Unique Song XYZ",
        "channel_title": "Concurrent Channel",
        "duration_sec": 210,
        "thumbnail": "",
    }

    def _fetch(vid: str):
        barrier.wait(timeout=5)
        return dict(meta)

    mock_fetch.side_effect = _fetch
    results: list[dict] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            results.append(adopt_youtube_result(conn, video_id="concurrvid1"))
        except BaseException as exc:  # noqa: BLE001 — collect for assertion
            errors.append(exc)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not errors, errors
    assert len(results) == 2
    assert results[0]["track_id"] == results[1]["track_id"]
    sources = conn.execute(
        """
        SELECT COUNT(*) FROM app_track_audio_source
        WHERE youtube_video_id = 'concurrvid1' OR source_ref = 'concurrvid1'
        """
    ).fetchone()[0]
    assert int(sources) == 1
    tracks = conn.execute(
        "SELECT COUNT(*) FROM dim_track WHERE nombre_track LIKE '%Concurrent Unique Song%'"
    ).fetchone()[0]
    assert int(tracks) == 1
    # Exactly one winner creates; the other reuses under the transactional re-check.
    assert sorted(r["reused_source"] for r in results) == [False, True]
