"""Tests for metadata normalization and query variants."""

from app.packages.streaming.services.audio.metadata_normalize import (
    build_search_query_variants,
    extract_youtube_video_id,
    normalize_track_meta,
    split_artists,
    strip_title_noise,
    title_variants,
)


def test_split_artists_semicolon_and_feat():
    artists = split_artists("Luis Fonsi; Daddy Yankee")
    assert artists == ["Luis Fonsi", "Daddy Yankee"]
    artists2 = split_artists("Artist A feat. Artist B")
    assert artists2[0] == "Artist A"
    assert "Artist B" in artists2
    artists3 = split_artists("A & B")
    assert artists3 == ["A", "B"]


def test_strip_remastered_and_year():
    assert "Remastered" not in strip_title_noise("Hello (Remastered 2011)")
    assert "2011" not in strip_title_noise("Hello (Remastered 2011)")
    assert strip_title_noise("Song - Deluxe Edition").lower().find("deluxe") < 0


def test_title_variants_keep_original():
    variants = title_variants("Billie Jean (Remastered 2003)")
    assert variants[0] == "Billie Jean (Remastered 2003)"
    assert any("Billie Jean" == v or v.startswith("Billie Jean") for v in variants)


def test_query_variants_multi_artist():
    qs = build_search_query_variants(
        "Despacito", "Luis Fonsi; Daddy Yankee", max_variants=5
    )
    assert len(qs) <= 5
    assert any("official audio" in q.lower() for q in qs)
    assert any("Luis Fonsi" in q and "Daddy Yankee" in q for q in qs)
    assert any('"' in q for q in qs)
    meta = normalize_track_meta("Despacito", "Luis Fonsi; Daddy Yankee")
    assert meta.primary_artist == "Luis Fonsi"
    assert len(meta.artists) == 2


def test_extract_youtube_video_id():
    assert extract_youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert (
        extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        == "dQw4w9WgXcQ"
    )
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("short") is None
    assert extract_youtube_video_id("https://example.com/watch?v=nope") is None
