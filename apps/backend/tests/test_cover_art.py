"""Unit tests for cover-art URL handling (no network)."""

import duckdb

from app.packages.streaming.services.cover_art_service import (
    cover_urls_for_tracks,
    get_cached_cover,
    upscale_artwork,
)


def test_upscale_artwork_replaces_size():
    src = "https://is1-ssl.mzstatic.com/image/thumb/abc/100x100bb.jpg"
    out = upscale_artwork(src)
    assert "600x600bb" in out
    assert "100x100bb" not in out


def test_upscale_artwork_noop_when_no_match():
    src = "https://example.com/cover.jpg"
    assert upscale_artwork(src) == src


def test_upscale_artwork_empty():
    assert upscale_artwork("") == ""


def test_catalog_cover_remains_authoritative_over_legacy_source():
    conn = duckdb.connect(":memory:")
    try:
        conn.execute(
            "CREATE TABLE app_track_cover "
            "(track_id BIGINT, image_url VARCHAR, status VARCHAR, resolved_at TIMESTAMP)"
        )
        conn.execute(
            "CREATE TABLE app_track_audio_source "
            "(track_id BIGINT, provider VARCHAR, youtube_video_id VARCHAR, "
            "source_ref VARCHAR, status VARCHAR)"
        )
        conn.execute(
            "INSERT INTO app_track_cover VALUES (7, 'https://wrong.example/africa.jpg', 'ok', NOW())"
        )
        conn.execute(
            "INSERT INTO app_track_audio_source VALUES (7, 'youtube', 'Kb7lAMjFuA0', NULL, 'ok')"
        )

        expected = "https://wrong.example/africa.jpg"
        assert get_cached_cover(conn, 7)["image_url"] == expected
        assert cover_urls_for_tracks(conn, [7]) == {7: expected}
    finally:
        conn.close()
