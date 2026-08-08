"""Tests for multi-provider AudioResolver."""

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from app.packages.streaming.services.audio.audius_provider import AudiusProvider
from app.packages.streaming.services.audio.cache import (
    STATUS_NOT_FOUND,
    STATUS_OK,
    is_cache_usable,
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


def test_cache_stores_confirmed_youtube_source(conn):
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    yt.resolve.return_value = ResolvedSource(
        track_id=10,
        provider="youtube",
        status=STATUS_OK,
        source_ref="vidOK12345",
        youtube_video_id="vidOK12345",
        query="Test Song Test Artist official audio",
        confidence_score=0.91,
    )
    resolver = AudioResolver(providers=[yt])
    result = resolver.resolve(conn, 10, force=True)
    assert result is not None
    assert result.status == STATUS_OK
    cached = read_cache(conn, 10)
    assert cached["youtube_video_id"] == "vidOK12345"
    assert cached["status"] == STATUS_OK


def test_manual_youtube_override_cached(conn):
    from unittest.mock import patch

    from app.packages.streaming.services.audio_source_service import (
        save_manual_youtube_source,
    )

    with patch(
        "app.packages.streaming.services.audio_source_service.validate_youtube_video_id",
        return_value="valid",
    ):
        out = save_manual_youtube_source(
            conn, 10, video_id_or_url="https://youtu.be/abcdefghijk"
        )
    assert out is not None
    assert out["status"] == STATUS_OK
    assert out["youtube_video_id"] == "abcdefghijk"
    cached = read_cache(conn, 10)
    assert cached["query"].startswith("manual:")


def test_mark_unavailable_caches_not_found(conn):
    from app.packages.streaming.services.audio_source_service import (
        mark_audio_unavailable,
    )

    out = mark_audio_unavailable(conn, 10, reason="ops")
    assert out["status"] == STATUS_NOT_FOUND
    cached = read_cache(conn, 10)
    assert cached["status"] == STATUS_NOT_FOUND


def test_truly_unavailable_when_providers_empty(conn):
    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    yt.resolve.return_value = ResolvedSource(
        track_id=10, provider="youtube", status=STATUS_NOT_FOUND, query="q"
    )
    aud = MagicMock(spec=AudiusProvider)
    aud.name = "audius"
    aud.resolve.return_value = ResolvedSource(
        track_id=10, provider="audius", status=STATUS_NOT_FOUND, query="q"
    )
    resolver = AudioResolver(providers=[yt, aud])
    result = resolver.resolve(conn, 10, force=True)
    assert result.status == STATUS_NOT_FOUND
    # Persist via write_cache path used by resolve()
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["status"] == STATUS_NOT_FOUND


def test_write_cache_resets_failure_count_on_ok(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            source_ref="failvid0001",
            youtube_video_id="failvid0001",
            query="q",
            confidence_score=0.9,
        ),
    )
    conn.execute(
        "UPDATE app_track_audio_source SET failure_count = 3 WHERE track_id = 10"
    )
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["failure_count"] == 3
    assert is_cache_usable(cached) is False

    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            source_ref="failvid0001",
            youtube_video_id="failvid0001",
            query="q-retry",
            confidence_score=0.95,
        ),
    )
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["failure_count"] == 0
    assert is_cache_usable(cached) is True


def test_write_cache_preserve_failure_count(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            source_ref="failvid0002",
            youtube_video_id="failvid0002",
            query="q",
            confidence_score=0.9,
        ),
    )
    conn.execute(
        "UPDATE app_track_audio_source SET failure_count = 2 WHERE track_id = 10"
    )
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            source_ref="failvid0002",
            youtube_video_id="failvid0002",
            query="metadata refresh",
            confidence_score=0.95,
        ),
        preserve_failure_count=True,
    )
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["failure_count"] == 2
    assert cached["query"] == "metadata refresh"


def test_local_published_never_overwritten(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="local_published",
            status=STATUS_OK,
            playable_url="/api/v1/media/1/content",
            source_ref="1",
        ),
    )
    # write_cache itself must refuse to replace local_published.
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            youtube_video_id="shouldNotWin",
            source_ref="shouldNotWin",
        ),
    )
    assert read_cache(conn, 10)["provider"] == "local_published"

    yt = MagicMock(spec=YouTubeProvider)
    yt.name = "youtube"
    yt.resolve.return_value = ResolvedSource(
        track_id=10,
        provider="youtube",
        status=STATUS_OK,
        youtube_video_id="shouldNotWin",
        source_ref="shouldNotWin",
    )
    resolver = AudioResolver(providers=[yt])
    result = resolver.resolve(conn, 10, force=True)
    assert result.provider == "local_published"
    yt.resolve.assert_not_called()
    cached = read_cache(conn, 10)
    assert cached["provider"] == "local_published"


def test_write_cache_local_published_can_replace_external(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="youtube",
            status=STATUS_OK,
            youtube_video_id="extvid00001",
            source_ref="extvid00001",
            query="q",
        ),
    )
    assert read_cache(conn, 10)["provider"] == "youtube"
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="local_published",
            status=STATUS_OK,
            playable_url="/api/v1/media/1/content",
            source_ref="1",
        ),
    )
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["provider"] == "local_published"
    assert cached["playable_url"] == "/api/v1/media/1/content"
    assert cached["failure_count"] == 0


def test_write_cache_new_insert_starts_failure_count_zero(conn):
    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="audius",
            status=STATUS_OK,
            source_ref="aud1",
            query="q",
        ),
    )
    assert read_cache(conn, 10)["failure_count"] == 0


def test_write_cache_local_published_protected_under_concurrent_external_writes(conn):
    """Atomic UPSERT: local_published must survive interleaved external upserts."""
    import threading

    from app.core.database import transactional

    write_cache(
        conn,
        ResolvedSource(
            track_id=10,
            provider="local_published",
            status=STATUS_OK,
            playable_url="/api/v1/media/1/content",
            source_ref="1",
        ),
    )
    errors: list[BaseException] = []

    def spam_external(provider: str, vid: str) -> None:
        try:
            for i in range(25):
                # Serialize shared-conn access like production; UPSERT itself is atomic.
                with transactional(conn):
                    write_cache(
                        conn,
                        ResolvedSource(
                            track_id=10,
                            provider=provider,
                            status=STATUS_OK,
                            youtube_video_id=f"{vid}{i:02d}" if provider == "youtube" else None,
                            source_ref=f"{vid}{i:02d}",
                            query=f"race-{provider}-{i}",
                        ),
                    )
        except BaseException as exc:  # noqa: BLE001 — surface in parent thread
            errors.append(exc)

    threads = [
        threading.Thread(target=spam_external, args=("youtube", "yt")),
        threading.Thread(target=spam_external, args=("audius", "au")),
        threading.Thread(target=spam_external, args=("youtube", "ytb")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    cached = read_cache(conn, 10)
    assert cached is not None
    assert cached["provider"] == "local_published"
    assert cached["playable_url"] == "/api/v1/media/1/content"
