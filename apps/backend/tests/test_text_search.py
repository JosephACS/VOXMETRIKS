"""Tests for accent-insensitive token search."""

from app.packages.streaming.services.text_search import fold_text, search_tokens


def test_fold_strips_accents() -> None:
    assert fold_text("Vámonos a Marte") == "vamonos a marte"


def test_search_tokens_drop_stopwords() -> None:
    assert search_tokens("vamonos a marte") == ["vamonos", "marte"]
    assert search_tokens("  GOLDEN   dreams  ") == ["golden", "dreams"]
