"""Unit tests for strengthened YouTube scoring / ranking."""

from app.packages.streaming.services.audio.youtube_scoring import (
    build_search_query,
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
    track_ms = 210_000
    assert (
        score_youtube_candidate(
            "Despacito Lyrics Video",
            video_duration_sec=210,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
        )
        < 0
    )
    assert (
        score_youtube_candidate(
            "Despacito - Cover by Random Band",
            video_duration_sec=210,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
        )
        < 0
    )


def test_prefers_official_with_matching_duration():
    track_ms = 210_000
    official = score_youtube_candidate(
        "Despacito (Official Audio)",
        video_duration_sec=212,
        track_duration_ms=track_ms,
        expected_title="Despacito",
        expected_artists=["Luis Fonsi"],
        channel_title="Luis Fonsi",
    )
    plain = score_youtube_candidate(
        "Despacito audio",
        video_duration_sec=212,
        track_duration_ms=track_ms,
        expected_title="Despacito",
        expected_artists=["Luis Fonsi"],
        channel_title="Luis Fonsi",
    )
    assert official > plain


def test_rejects_incompatible_duration():
    track_ms = 210_000
    assert (
        score_youtube_candidate(
            "Despacito Official Audio",
            video_duration_sec=45,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
        )
        < 0
    )
    assert (
        score_youtube_candidate(
            "Despacito Official Audio",
            video_duration_sec=3600,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
        )
        < 0
    )


def test_rejects_incompatible_artist():
    track_ms = 210_000
    assert (
        score_youtube_candidate(
            "Despacito Official Audio",
            video_duration_sec=210,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
            channel_title="Totally Different Channel XYZ",
        )
        < 0
    )


def test_rejects_weak_title():
    track_ms = 210_000
    assert (
        score_youtube_candidate(
            "Random Unrelated Upload Official Audio",
            video_duration_sec=210,
            track_duration_ms=track_ms,
            expected_title="Despacito",
            expected_artists=["Luis Fonsi"],
            channel_title="Luis Fonsi",
        )
        < 0
    )


def test_rejects_unavailable_status_in_pick():
    track_ms = 200_000
    chosen = pick_best_youtube_candidate(
        [
            {
                "video_id": "gone",
                "title": "Song — Official Audio",
                "duration_sec": 200,
                "availability": "unavailable",
                "channel_title": "Artist",
            },
            {
                "video_id": "good",
                "title": "Song — Official Audio",
                "duration_sec": 198,
                "channel_title": "Artist",
            },
        ],
        track_ms,
        expected_title="Song",
        expected_artists=["Artist"],
    )
    assert chosen == "good"


def test_pick_best_among_candidates():
    track_ms = 200_000
    chosen = pick_best_youtube_candidate(
        [
            {"video_id": "bad1", "title": "Song Lyrics", "duration_sec": 200},
            {"video_id": "bad2", "title": "Song Cover", "duration_sec": 200},
            {
                "video_id": "good",
                "title": "Song — Official Audio",
                "duration_sec": 198,
                "channel_title": "The Artist",
            },
            {
                "video_id": "live",
                "title": "Song Live at Madison Square Garden",
                "duration_sec": 420,
            },
        ],
        track_ms,
        expected_title="Song",
        expected_artists=["The Artist"],
    )
    assert chosen == "good"


def test_remastered_catalog_title_matches_clean_official():
    track_ms = 240_000
    score = score_youtube_candidate(
        "Billie Jean (Official Audio)",
        video_duration_sec=242,
        track_duration_ms=track_ms,
        expected_title="Billie Jean (Remastered 2008)",
        expected_artists=["Michael Jackson"],
        channel_title="Michael Jackson",
    )
    assert score > 0


def test_multi_artist_query_includes_primary():
    q = build_search_query("Despacito", "Luis Fonsi; Daddy Yankee")
    assert "Luis Fonsi" in q
    assert "official audio" in q.lower()


def test_validate_youtube_no_oembed_without_key(monkeypatch):
    from app.packages.streaming.services import audio_source_service as svc

    class _S:
        youtube_api_key = ""

    monkeypatch.setattr("app.core.config.get_settings", lambda: _S())
    import httpx

    def _boom(*_a, **_k):
        raise AssertionError("oEmbed must not be used")

    monkeypatch.setattr(httpx, "get", _boom)
    assert svc.validate_youtube_video_id("dQw4w9WgXcQ") == "provider_unavailable"
    assert svc._validate_youtube_video_id("dQw4w9WgXcQ") is False


def test_validate_youtube_empty_items_is_invalid(monkeypatch):
    from app.packages.streaming.services import audio_source_service as svc
    from unittest.mock import MagicMock

    class _S:
        youtube_api_key = "k"

    monkeypatch.setattr("app.core.config.get_settings", lambda: _S())
    import httpx

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"items": []}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: resp)
    assert svc.validate_youtube_video_id("dQw4w9WgXcQ") == "invalid"


def test_validate_youtube_http_error_is_provider_unavailable(monkeypatch):
    from app.packages.streaming.services import audio_source_service as svc
    from unittest.mock import MagicMock

    class _S:
        youtube_api_key = "k"

    monkeypatch.setattr("app.core.config.get_settings", lambda: _S())
    import httpx

    resp = MagicMock()
    resp.status_code = 403
    monkeypatch.setattr(httpx, "get", lambda *a, **k: resp)
    assert svc.validate_youtube_video_id("dQw4w9WgXcQ") == "provider_unavailable"