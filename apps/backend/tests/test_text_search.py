"""Tests for accent-insensitive token search."""

from app.packages.streaming.services.text_search import (
    build_track_search_filter,
    fold_text,
    search_tokens,
)


def test_fold_strips_accents() -> None:
    assert fold_text("Vámonos a Marte") == "vamonos a marte"


def test_search_tokens_drop_stopwords() -> None:
    assert search_tokens("vamonos a marte") == ["vamonos", "marte"]
    assert search_tokens("  GOLDEN   dreams  ") == ["golden", "dreams"]


def test_track_search_uses_word_prefix_not_midword() -> None:
    """``meda`` must match Medallita, not accidental mid-word Someday."""
    sql, params = build_track_search_filter("meda", search_fold_col="sf")
    assert "LIKE ?" in sql
    assert "meda%" in params
    assert "% meda%" in params
    assert "%meda%" not in params
