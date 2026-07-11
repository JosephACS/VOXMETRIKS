"""Tests for multi-provider AudioResolver."""

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from app.packages.streaming.services.audio.audius_provider import AudiusProvider
from app.packages.streaming.services.audio.cache import (
    STATUS_NOT_FOUND,
    STATUS_OK,
    migrate_audio_source_columns,
    read_cache,
    write_cache,
)
from app.packages.streaming.services.audio.models import ResolvedSource, TrackContext
from app.packages.streaming.services.audio.resolver import AudioResolver
from app.packages.streaming.services.audio.youtube_provider import YouTubeProvider


@pytest.fixture
def conn():
    c = duckdb.connect(":memory:")
    c.execute("""
        CREATE TABLE dim_track (
            id_track INTEGER PRIMARY KEY,
            nombre_track VARCHAR,
            id_artista INTEGER,
            duration_ms INTEGER,
            nombre_album VARCHAR
        )
    """)
    c.execute("""
        CREATE TABLE dim_artista (
            id_artista INTEGER PRIMARY KEY,
            nombre_artista VARCHAR
        )
    """)
    c.execute("""
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
            resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_checked_at TIMESTAMP
        )
    """)
    c.execute("INSERT INTO dim_artista VALUES (1, 'Test Artist')")
    c.execute(
        "INSERT INTO dim_track VALUES (10, 'Test Song', 1, 180000, 'Test Album')"
    )
    return c


def test_cached_source_is_reused(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            source_ref="abc123",
            youtube_video_id="abc123",
            query="Test Song Test Artist official audio",
            confidence_score=0.9,
        ),
    )
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    resolver = AudioResolver(providers=[yt])
    result = resolver.resolve(conn, 10, force=False)
    assert result is not None
    assert result.status == STATUS_OK
    assert result.source_ref == "abc123"
    yt.resolve.assert_not_called()


def test_youtube_falls_back_to_audius(conn):
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    yt.resolve.return_value = ResolvedSource(
        track_id=10, provider="youtube", status=STATUS_NOT_FOUND, query="q"
    )
    aud = MagicMock(spec=AudiusProvider)
    aud.name = "audius"
    aud.resolve.return_value = ResolvedSource(
        track_id=10,
        provider="audius",
        status=STATUS_OK,
        source_ref="aud-1",
        playable_url="https://api.audius.co/v1/tracks/aud-1/stream",
        query="q",
        confidence_score=0.7,
    )
    resolver = AudioResolver(providers=[yt, aud])
    result = resolver.resolve(conn, 10, force=True)
    assert result is not None
    assert result.provider == "audius"
    assert result.playable_url is not None
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["provider"] == "audius"


def test_all_providers_fail_returns_not_found(conn):
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    yt.resolve.return_value = ResolvedSource(
        track_id=10, provider="youtube", status=STATUS_NOT_FOUND
    )
    aud = MagicMock(spec=AudiusProvider)
    aud.name = "audius"
    aud.resolve.return_value = ResolvedSource(
        track_id=10, provider="audius", status=STATUS_NOT_FOUND
    )
    resolver = AudioResolver(providers=[yt, aud])
    result = resolver.resolve(conn, 10, force=True)
    assert result is not None
    assert result.status == STATUS_NOT_FOUND


def test_skip_provider_on_fallback(conn):
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    aud = MagicMock(spec=AudiusProvider)
    aud.name = "audius"
    aud.resolve.return_value = ResolvedSource(
        track_id=10,
        provider="audius",
        status=STATUS_OK,
        source_ref="x",
        playable_url="https://example.com/stream",
    )
    resolver = AudioResolver(providers=[yt, aud])
    result = resolver.resolve(conn, 10, force=True, skip_provider="youtube")
    assert result is not None
    assert result.provider == "audius"
    yt.resolve.assert_not_called()


def test_migrate_audio_source_columns_idempotent(conn):
    migrate_audio_source_columns(conn)
    migrate_audio_source_columns(conn)
    cols = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'app_track_audio_source'"
        ).fetchall()
    }
    assert "playable_url" in cols
    assert "failure_count" in cols
