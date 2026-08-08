"""Normalize track/artist metadata and build search-query variants.

Used by YouTube/Audius providers — does not invent catalog data.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Sequence

# Solo separators for artist credit strings common in warehouse dims.
_ARTIST_SPLIT_RE = re.compile(
    r"\s*(?:;|,|\s&\s|(?:\bfeat\.?|\bft\.?|\bfeaturing)\s+)\s*",
    re.IGNORECASE,
)

# Parenthetical / bracket noise and remaster/edition/year tags.
_TITLE_NOISE_RE = re.compile(
    r"[\(\[\{]\s*(?:"
    r"re[- ]?master(?:ed)?(?:\s+\d{4})?|"
    r"(?:deluxe|special|expanded|anniversary|bonus|digital)\s+edition|"
    r"(?:radio|album|single|explicit|clean)\s+version|"
    r"(?:official\s+)?(?:music\s+)?video|"
    r"\d{4}|"
    r"remaster(?:ed)?|"
    r"version|"
    r"edition"
    r")\s*[\)\]\}]",
    re.IGNORECASE,
)

_YEAR_BARE_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_REMASTER_BARE_RE = re.compile(
    r"\b(?:re[- ]?master(?:ed)?|deluxe\s+edition|special\s+edition|"
    r"expanded\s+edition|anniversary\s+edition)\b",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")
_PUNCT_SOFT_RE = re.compile(r"[\"'`´""'']+")
_FEAT_IN_TITLE_RE = re.compile(
    r"\s*[\(\[]?\s*(?:feat\.?|ft\.?|featuring)\s+.+?[\)\]]?\s*$",
    re.IGNORECASE,
)

_MAX_QUERY_VARIANTS = 5


@dataclass(frozen=True)
class NormalizedTrackMeta:
    """Normalized metadata derived from warehouse track/artist strings."""

    original_title: str
    clean_title: str
    title_variants: tuple[str, ...]
    artists: tuple[str, ...]
    primary_artist: str
    all_artists_joined: str


def collapse_spaces(value: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", (value or "").strip())


def normalize_signs(value: str) -> str:
    """NFKC + soft punctuation cleanup without inventing new words."""
    text = unicodedata.normalize("NFKC", value or "")
    text = _PUNCT_SOFT_RE.sub("", text)
    text = text.replace("/", " ").replace("|", " ").replace("·", " ")
    return collapse_spaces(text)


def split_artists(artist_name: str) -> List[str]:
    """Split artists on ``;``, ``,``, ``&``, and ``feat./ft./featuring``."""
    raw = collapse_spaces(artist_name or "")
    if not raw:
        return []
    parts = [collapse_spaces(p) for p in _ARTIST_SPLIT_RE.split(raw) if collapse_spaces(p)]
    # Deduplicate preserving order (case-insensitive).
    seen: set[str] = set()
    out: List[str] = []
    for p in parts:
        key = p.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out or ([raw] if raw else [])


def strip_title_noise(title: str) -> str:
    """Remove remaster/year/edition/version tags while keeping core title words."""
    text = normalize_signs(title)
    text = _TITLE_NOISE_RE.sub(" ", text)
    text = _REMASTER_BARE_RE.sub(" ", text)
    text = _YEAR_BARE_RE.sub(" ", text)
    text = _FEAT_IN_TITLE_RE.sub(" ", text)
    return collapse_spaces(text)


def title_variants(original_title: str) -> List[str]:
    """Original-preserving variants (unique, non-empty)."""
    original = collapse_spaces(original_title or "")
    clean = normalize_signs(original)
    stripped = strip_title_noise(original)
    variants: List[str] = []
    for candidate in (original, clean, stripped):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def normalize_track_meta(track_name: str, artist_name: str) -> NormalizedTrackMeta:
    original = collapse_spaces(track_name or "")
    artists = split_artists(artist_name or "")
    primary = artists[0] if artists else ""
    joined = " ".join(artists)
    variants = title_variants(original)
    clean = variants[1] if len(variants) > 1 else (variants[0] if variants else "")
    return NormalizedTrackMeta(
        original_title=original,
        clean_title=clean or original,
        title_variants=tuple(variants),
        artists=tuple(artists),
        primary_artist=primary,
        all_artists_joined=joined,
    )


def build_search_query_variants(
    track_name: str,
    artist_name: str,
    *,
    max_variants: int = _MAX_QUERY_VARIANTS,
) -> List[str]:
    """Ordered search queries (title+artist strategies). Cap at ``max_variants``.

    Strategy (first available wins slots):
    1. title + primary artist + official audio
    2. title + all artists
    3. title + primary artist
    4. quoted title + artist
    5. normalized title variant (+ primary artist / official when possible)
    """
    meta = normalize_track_meta(track_name, artist_name)
    title = meta.original_title or meta.clean_title
    if not title:
        return []

    primary = meta.primary_artist
    all_artists = meta.all_artists_joined
    stripped = (
        meta.title_variants[-1]
        if meta.title_variants and meta.title_variants[-1] != title
        else meta.clean_title
    )

    candidates: List[str] = []

    def add(q: str) -> None:
        q = collapse_spaces(q)
        if q and q not in candidates:
            candidates.append(q)

    if primary:
        add(f"{title} {primary} official audio")
    else:
        add(f"{title} official audio")

    if all_artists and all_artists.casefold() != primary.casefold():
        add(f"{title} {all_artists}")

    if primary:
        add(f"{title} {primary}")
    else:
        add(title)

    if primary:
        add(f'"{title}" {primary}')
    else:
        add(f'"{title}"')

    if stripped and stripped.casefold() != title.casefold():
        if primary:
            add(f"{stripped} {primary} official audio")
        else:
            add(f"{stripped} official audio")

    return candidates[: max(1, max_variants)]


def token_set(text: str) -> set[str]:
    return {t for t in re.split(r"[^\w]+", (text or "").casefold()) if len(t) > 1}


def title_similarity(candidate_title: str, expected_title: str) -> float:
    """Jaccard-like token overlap in [0, 1]."""
    a = token_set(strip_title_noise(candidate_title) or candidate_title)
    b = token_set(strip_title_noise(expected_title) or expected_title)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def artist_match_score(candidate_text: str, artists: Sequence[str]) -> float:
    """How well candidate (title+channel/artist) matches expected artists.

    Returns 0..1. Empty expected artists → neutral 0.5 (do not hard-fail).
    """
    if not artists:
        return 0.5
    hay = (candidate_text or "").casefold()
    if not hay:
        return 0.0
    hits = 0
    for artist in artists:
        tokens = token_set(artist)
        if not tokens:
            continue
        # Require majority of artist tokens present.
        present = sum(1 for t in tokens if t in hay)
        if present >= max(1, (len(tokens) + 1) // 2):
            hits += 1
    if hits == 0:
        # Weak substring of primary artist name
        primary = artists[0].casefold()
        if len(primary) >= 4 and primary in hay:
            return 0.35
        return 0.0
    return min(1.0, hits / len(artists) + (0.25 if hits >= 1 else 0.0))


def extract_youtube_video_id(raw: str) -> Optional[str]:
    """Accept bare 11-char IDs or common YouTube URL forms."""
    text = (raw or "").strip()
    if not text:
        return None
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", text):
        return text
    patterns = (
        r"(?:youtube\.com/watch\?[^#]*v=|youtu\.be/|youtube\.com/embed/|"
        r"youtube\.com/shorts/|youtube\.com/live/)([A-Za-z0-9_-]{11})",
    )
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None
