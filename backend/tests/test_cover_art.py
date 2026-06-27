"""Unit tests for cover-art URL handling (no network)."""

from app.packages.streaming.services.cover_art_service import upscale_artwork


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
