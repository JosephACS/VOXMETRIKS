# -*- coding: utf-8 -*-
"""Musical compatibility between YouTube metadata and catalog tracks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional, Set

from app.packages.catalog.services.text_search import fold_text

# Strip from matching noise (do not strip version differentiators).
_NOISE = frozenset({
    "official", "audio", "video", "lyrics", "lyric", "visualizer", "visualiser",
    "remastered", "remaster", "hd", "hq", "4k", "music", "topic", "vevo",
    "original", "song", "mv", "clip",
})

_STOP = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
})

# Must agree between source and track (or both absent).
_VERSION_MARKERS = frozenset({
    "remix", "live", "acoustic", "instrumental", "slowed", "sped", "speed",
    "cover", "karaoke", "nightcore", "reverb",
})

_FEAT = re.compile(r"\b(feat\.?|ft\.?|featuring)\b", re.I)


@dataclass(frozen=True)
class MusicIdentity:
    title_core: str
    title_tokens: frozenset[str]
    artist_tokens: frozenset[str]
    version_markers: frozenset[str]
    duration_ms: Optional[int] = None


def _tokenize(text: str) -> Set[str]:
    folded = fold_text(text or "")
    folded = _FEAT.sub(" ", folded)
    folded = re.sub(r"[^a-z0-9À-ÿ]+", " ", folded, flags=re.I)
    out: Set[str] = set()
    for t in folded.split():
        if len(t) < 2:
            continue
        if t in _NOISE or t in _STOP:
            continue
        out.add(t)
    return out


def _versions(tokens: Iterable[str]) -> Set[str]:
    found: Set[str] = set()
    for t in tokens:
        if t in _VERSION_MARKERS:
            found.add(t)
        if t in {"sped", "speed"}:
            found.add("sped")
    return found


def parse_youtube_display(title: str, channel_title: str = "") -> tuple[str, str]:
    """Best-effort split of 'Artist - Song' YouTube titles."""
    raw = (title or "").strip()
    channel = (channel_title or "").strip()
    for sep in (" - ", " – ", " — ", " | "):
        if sep in raw:
            left, right = raw.split(sep, 1)
            left, right = left.strip(), right.strip()
            if left and right:
                return right, left
    return raw, channel


def build_identity_from_youtube(
    *,
    title: str,
    channel_title: str = "",
    duration_ms: Optional[int] = None,
) -> MusicIdentity:
    song, artist_guess = parse_youtube_display(title, channel_title)
    title_tokens = _tokenize(song)
    core_tokens = frozenset(t for t in title_tokens if t not in _VERSION_MARKERS)
    # Prefer artist parsed from title; do not pollute with unrelated channel names
    if artist_guess and artist_guess.strip().lower() != (channel_title or "").strip().lower():
        artist_tokens = frozenset(
            t for t in _tokenize(artist_guess) if t not in _VERSION_MARKERS
        )
    else:
        artist_tokens = frozenset(
            t
            for t in _tokenize(channel_title or artist_guess)
            if t not in _VERSION_MARKERS
        )
    versions = frozenset(_versions(title_tokens) | _versions(_tokenize(title)))
    return MusicIdentity(
        title_core=" ".join(sorted(core_tokens)),
        title_tokens=frozenset(core_tokens),
        artist_tokens=artist_tokens,
        version_markers=versions,
        duration_ms=duration_ms,
    )


def build_identity_from_track(
    *,
    title: str,
    artist: str = "",
    duration_ms: Optional[int] = None,
) -> MusicIdentity:
    title_tokens = _tokenize(title)
    core_tokens = frozenset(t for t in title_tokens if t not in _VERSION_MARKERS)
    artist_tokens = frozenset()
    for part in re.split(r"[;,/&]| featuring | feat\.? | ft\.? ", artist or "", flags=re.I):
        artist_tokens |= _tokenize(part)
    artist_tokens = frozenset(t for t in artist_tokens if t not in _VERSION_MARKERS)
    versions = frozenset(_versions(title_tokens))
    return MusicIdentity(
        title_core=" ".join(sorted(core_tokens)),
        title_tokens=frozenset(core_tokens),
        artist_tokens=artist_tokens,
        version_markers=versions,
        duration_ms=duration_ms,
    )


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def artist_overlap(track: MusicIdentity, source: MusicIdentity) -> float:
    return _jaccard(set(track.artist_tokens), set(source.artist_tokens))


def versions_compatible(a: Set[str], b: Set[str]) -> bool:
    """Same recording family: markers must not conflict."""
    if not a and not b:
        return True
    if a != b:
        if a and b and a != b:
            return False
        if (a and not b) or (b and not a):
            return False
    return True


def is_strong_match(track: MusicIdentity, source: MusicIdentity) -> bool:
    if not versions_compatible(set(track.version_markers), set(source.version_markers)):
        return False
    title_score = _jaccard(set(track.title_tokens), set(source.title_tokens))
    if title_score < 0.55:
        return False
    if title_score < 0.85:
        smaller, larger = (
            (track.title_tokens, source.title_tokens)
            if len(track.title_tokens) <= len(source.title_tokens)
            else (source.title_tokens, track.title_tokens)
        )
        if smaller and not smaller.issubset(larger):
            return False

    # When both sides declare artists, require real overlap (never title-only).
    if track.artist_tokens and source.artist_tokens:
        if not (track.artist_tokens & source.artist_tokens):
            return False
    elif track.artist_tokens and not source.artist_tokens and title_score < 0.95:
        return False

    if track.duration_ms and source.duration_ms:
        diff = abs(int(track.duration_ms) - int(source.duration_ms))
        longer = max(int(track.duration_ms), int(source.duration_ms))
        if longer > 0 and diff > max(90_000, int(longer * 0.45)):
            return False
    return True


def is_incompatible(track: MusicIdentity, source: MusicIdentity) -> bool:
    """True when titles clearly refer to different songs (or same title, wrong artist)."""
    if not versions_compatible(set(track.version_markers), set(source.version_markers)):
        return True
    title_score = _jaccard(set(track.title_tokens), set(source.title_tokens))
    if title_score <= 0.2 and track.title_tokens and source.title_tokens:
        return True
    if (
        title_score >= 0.7
        and track.artist_tokens
        and source.artist_tokens
        and not (track.artist_tokens & source.artist_tokens)
    ):
        return True
    return False
