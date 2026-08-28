"""Unit tests for the unauthenticated Deezer preview resolver."""

from unittest.mock import MagicMock, patch

from app.packages.streaming.services.audio.cache import STATUS_NOT_FOUND, STATUS_OK
from app.packages.streaming.services.audio.deezer_provider import DeezerProvider
from app.packages.streaming.services.audio.models import TrackContext


def _track() -> TrackContext:
    return TrackContext(
        track_id=7,
        track_name="Test Song",
        artist_name="Test Artist",
        duration_ms=180_000,
    )


def test_resolves_track_specific_preview_url():
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "data": [
            {
                "id": 123,
                "title": "Test Song",
                "duration": 181,
                "preview": "https://cdns-preview.dzcdn.net/stream-123.mp3",
                "artist": {"name": "Test Artist"},
            }
        ]
    }
    with patch(
        "app.packages.streaming.services.audio.deezer_provider.httpx.get",
        return_value=response,
    ) as get:
        result = DeezerProvider().resolve(_track())

    assert result.status == STATUS_OK
    assert result.provider == "deezer"
    assert result.source_ref == "123"
    assert result.playable_url.endswith("stream-123.mp3")
    assert get.call_args.kwargs["params"]["limit"] == 10


def test_rejects_wrong_artist_or_missing_preview():
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "data": [
            {
                "id": 999,
                "title": "Test Song",
                "duration": 180,
                "preview": "https://cdns-preview.dzcdn.net/wrong.mp3",
                "artist": {"name": "Another Artist"},
            },
            {
                "id": 1000,
                "title": "Test Song",
                "duration": 180,
                "preview": None,
                "artist": {"name": "Test Artist"},
            },
        ]
    }
    with patch(
        "app.packages.streaming.services.audio.deezer_provider.httpx.get",
        return_value=response,
    ):
        result = DeezerProvider().resolve(_track())

    assert result.status == STATUS_NOT_FOUND
