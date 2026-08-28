"""YouTube candidate scoring — academic playback matching rules."""
from __future__ import annotations

from types import SimpleNamespace

from app.packages.streaming.services.audio.youtube_scoring import (
    is_youtube_music_candidate,
    pick_best_youtube_candidate_detailed,
    score_youtube_candidate,
    youtube_music_origin,
)
from app.packages.streaming.services.audio.youtube_provider import YouTubeProvider


def test_recognizes_youtube_music_catalog_signals_and_rejects_generic_uploads():
    assert youtube_music_origin(
        title="505",
        channel_title="Arctic Monkeys - Topic",
        category_id="10",
    ) == "art_track"
    assert youtube_music_origin(
        title="Artist - Song",
        channel_title="Artist",
        category_id="10",
        licensed_content=True,
    ) == "licensed"
    assert youtube_music_origin(
        title="Artist - Song (Official Music Video)",
        channel_title="Artist",
        category_id="10",
    ) == "official"
    assert not is_youtube_music_candidate(
        {
            "title": "Artist - Song lyrics español",
            "channel_title": "Fan Lyrics",
            "category_id": "10",
            "licensed_content": False,
        }
    )
    assert not is_youtube_music_candidate(
        {
            "title": "Artist - Song (Official Audio)",
            "channel_title": "Artist",
            "category_id": "22",
            "licensed_content": True,
        }
    )


def test_catalog_signal_prioritizes_art_track_over_generic_candidate():
    topic = score_youtube_candidate(
        "Arctic Monkeys - 505",
        video_duration_sec=253,
        track_duration_ms=253000,
        expected_title="505",
        expected_artists=["Arctic Monkeys"],
        channel_title="Arctic Monkeys - Topic",
        category_id="10",
        music_origin="art_track",
    )
    generic = score_youtube_candidate(
        "Arctic Monkeys - 505",
        video_duration_sec=253,
        track_duration_ms=253000,
        expected_title="505",
        expected_artists=["Arctic Monkeys"],
        channel_title="Fan Channel",
    )

    assert topic > generic


def test_free_text_search_keeps_official_result_when_query_contains_artist(monkeypatch):
    provider = YouTubeProvider()
    monkeypatch.setattr(
        "app.packages.streaming.services.audio.youtube_provider.get_settings",
        lambda: SimpleNamespace(youtube_api_key="test-key"),
    )
    monkeypatch.setattr(
        provider,
        "_collect_candidates",
        lambda _q, _key: [
            {
                "video_id": "official-id",
                "title": "Taylor Swift - The Fate of Ophelia (Official Music Video)",
                "channel_title": "Taylor Swift",
                "duration_sec": 239,
                "category_id": "10",
                "music_origin": "official",
            },
            {
                "video_id": "short-id",
                "title": "The Fate of Ophelia official clip",
                "channel_title": "Promo Channel",
                "duration_sec": 20,
                "category_id": "10",
                "music_origin": "official",
            },
        ],
    )

    rows = provider.search_query_candidates(
        "The Fate of Ophelia Taylor Swift",
        expected_title="The Fate of Ophelia Taylor Swift",
        expected_artists=[],
    )

    assert [row["video_id"] for row in rows] == ["official-id"]


def test_artist_name_ending_in_ft_is_not_mistaken_for_featuring_credit():
    score = score_youtube_candidate(
        "Taylor Swift - The Fate of Ophelia (Official Music Video)",
        video_duration_sec=239,
        track_duration_ms=None,
        expected_title="The Fate of Ophelia",
        expected_artists=["Taylor Swift"],
        channel_title="Taylor Swift",
        category_id="10",
        music_origin="official",
    )

    assert score > 0


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


def test_recovery_can_use_matching_lyrics_after_primary_sources_fail():
    candidates = [
        {
            "video_id": "lyrics-id",
            "title": "Toto - Africa (Lyrics)",
            "channel_title": "Lyrics Channel",
            "duration_sec": 295,
        }
    ]

    strict = pick_best_youtube_candidate_detailed(
        candidates,
        295000,
        expected_title="Africa",
        expected_artists=["Toto"],
    )
    recovered = pick_best_youtube_candidate_detailed(
        candidates,
        295000,
        expected_title="Africa",
        expected_artists=["Toto"],
        min_accept_score=0.0,
        allow_secondary_variants=True,
    )

    assert strict is None
    assert recovered is not None
    assert recovered["video_id"] == "lyrics-id"


def test_provider_accepts_matching_lyrics_on_initial_catalog_resolution(monkeypatch):
    provider = YouTubeProvider()
    candidates = [
        {
            "video_id": "ik-tera-exact",
            "title": "Maninder Buttar - IK TERA [Lyrics]",
            "channel_title": "Be Free Music",
            "duration_sec": 161,
        },
        {
            "video_id": "wrong-cover",
            "title": "Ik Tera acoustic cover",
            "channel_title": "Cover Sessions",
            "duration_sec": 212,
        },
    ]
    monkeypatch.setattr(provider, "_search_api_raw", lambda _q, _key: (candidates, True))

    picked, ok, _ranked = provider._search_api(
        "Ik Tera Maninder Buttar",
        "test-key",
        160_768,
        expected_title="Ik Tera",
        expected_artists=["Maninder Buttar"],
    )

    assert ok is True
    assert picked is not None
    assert picked["video_id"] == "ik-tera-exact"
