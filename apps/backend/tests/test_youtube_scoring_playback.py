"""YouTube candidate scoring — academic playback matching rules."""
from __future__ import annotations

from app.packages.streaming.services.audio.youtube_scoring import score_youtube_candidate


def test_prefers_official_audio_over_cover():
    official = score_youtube_candidate(
        "Ed Sheeran - Shape of You (Official Audio)",
        video_duration_sec=233,
        track_duration_ms=233000,
        expected_title="Shape of You",
        expected_artists=["Ed Sheeran"],
        channel_title="Ed Sheeran",
    )
    cover = score_youtube_candidate(
        "Shape of You - Karaoke Cover",
        video_duration_sec=240,
        track_duration_ms=233000,
        expected_title="Shape of You",
        expected_artists=["Ed Sheeran"],
        channel_title="Karaoke Channel",
    )
    assert official > 0
    assert cover < 0  # hard reject cover unless catalog asks for it
    assert official > cover


def test_extreme_duration_mismatch_rejected():
    ok = score_youtube_candidate(
        "Adele - Hello Official Audio",
        video_duration_sec=295,
        track_duration_ms=295000,
        expected_title="Hello",
        expected_artists=["Adele"],
        channel_title="AdeleVEVO",
    )
    bad = score_youtube_candidate(
        "Adele - Hello Official Audio",
        video_duration_sec=90,
        track_duration_ms=295000,
        expected_title="Hello",
        expected_artists=["Adele"],
        channel_title="AdeleVEVO",
    )
    assert ok > 0
    assert bad < 0
