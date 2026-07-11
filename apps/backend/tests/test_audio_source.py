"""Unit tests for YouTube audio-source scoring (no API key required)."""

from app.packages.streaming.services.audio.youtube_scoring import (
    parse_iso8601_duration,
    pick_best_youtube_candidate,
    score_youtube_candidate,
)


def test_parse_iso8601_duration():
    assert parse_iso8601_duration("PT3M30S") == 210
    assert parse_iso8601_duration("PT1H2M3S") == 3723
    assert parse_iso8601_duration("PT45S") == 45
    assert parse_iso8601_duration("") == 0


def test_rejects_lyric_and_cover_titles():
    track_ms = 210_000  # 3:30
    assert score_youtube_candidate(
        "Despacito Lyrics Video",
        video_duration_sec=210,
        track_duration_ms=track_ms,
    ) < 0
    assert score_youtube_candidate(
        "Despacito - Cover by Random Band",
        video_duration_sec=210,
        track_duration_ms=track_ms,
    ) < 0


def test_prefers_official_with_matching_duration():
    track_ms = 210_000
    official = score_youtube_candidate(
        "Despacito (Official Audio)",
        video_duration_sec=212,
        track_duration_ms=track_ms,
    )
    plain = score_youtube_candidate(
        "Despacito audio",
        video_duration_sec=212,
        track_duration_ms=track_ms,
    )
    assert official > plain


def test_rejects_too_short_or_too_long():
    track_ms = 210_000
    assert score_youtube_candidate(
        "Despacito Official Audio",
        video_duration_sec=45,
        track_duration_ms=track_ms,
    ) < 0
    assert score_youtube_candidate(
        "Despacito Official Audio 1 hour loop",
        video_duration_sec=3600,
        track_duration_ms=track_ms,
    ) < 0


def test_pick_best_among_candidates():
    track_ms = 200_000  # 3:20
    chosen = pick_best_youtube_candidate(
        [
            {"video_id": "bad1", "title": "Song Lyrics", "duration_sec": 200},
            {"video_id": "bad2", "title": "Song Cover", "duration_sec": 200},
            {
                "video_id": "good",
                "title": "Song — Official Audio",
                "duration_sec": 198,
            },
            {
                "video_id": "live",
                "title": "Song Live at Madison Square Garden",
                "duration_sec": 420,
            },
        ],
        track_ms,
    )
    assert chosen == "good"
