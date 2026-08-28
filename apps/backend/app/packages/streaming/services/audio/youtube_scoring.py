"""YouTube search query + candidate scoring / ranking."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from .metadata_normalize import (
    artist_match_score,
    build_search_query_variants,
    normalize_track_meta,
    strip_title_noise,
    title_similarity,
)

# Backwards-compatible single-query helper (used by service facade).
def build_search_query(track_name: str, artist_name: str) -> str:
    variants = build_search_query_variants(track_name, artist_name)
    return variants[0] if variants else f"{track_name} official audio".strip()


_BAD_TITLE_RE = re.compile(
    r"\b("
    r"cover|covers|"
    r"lyric(?:s| video)?|letras|subtitulad[oa]|sub(?:\.|\s)?esp|"
    r"karaoke|instrumental(?: cover)?|"
    r"remix|re[- ]?mix|mashup|"
    r"live(?: at| from| performance| version| @)?|"
    r"acoustic(?: version| cover)?|unplugged|"
    r"sped[\s-]?up|slowed(?:[\s-]?reverb)?|nightcore|8d audio|bass boosted|"
    r"1[\s-]?hour|10[\s-]?hours|hour loop|loop|extended mix|"
    r"fan[\s-]?made|reaction|tutorial|how to play|"
    r"tik[\s-]?tok|shorts|clip|trailer|teaser"
    r")\b",
    re.IGNORECASE,
)

_GOOD_TITLE_RE = re.compile(
    r"\b(official(?: audio| video| music video| mv| visualizer)?|"
    r"provided to youtube|vevo|topic)\b",
    re.IGNORECASE,
)

_TOPIC_CHANNEL_RE = re.compile(r"(?:-|–|—)\s*topic\s*$", re.IGNORECASE)
_VEVO_CHANNEL_RE = re.compile(r"vevo\s*$", re.IGNORECASE)
_OFFICIAL_MUSIC_RE = re.compile(
    r"\b(official\s+(?:audio|video|music\s+video|lyric\s+video|visualizer)|"
    r"provided\s+to\s+youtube)\b",
    re.IGNORECASE,
)
_OFFICIAL_CHANNEL_RE = re.compile(r"\bofficial\s*$", re.IGNORECASE)

_EXPLICIT_VARIANT_RE = re.compile(
    r"\b(live|cover|remix|karaoke|slowed|nightcore|sped[\s-]?up)\b",
    re.IGNORECASE,
)

_ISO8601_DURATION_RE = re.compile(
    r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)

# Absolute reject thresholds (never auto-accept these).
_MIN_TITLE_SIM = 0.22
_MIN_ARTIST_SCORE = 0.30
_MIN_ACCEPT_SCORE = 25.0


def youtube_music_origin(
    *,
    title: str = "",
    channel_title: str = "",
    category_id: str = "",
    licensed_content: bool = False,
) -> str:
    """Classify high-confidence music-catalog videos returned by YouTube.

    YouTube does not expose public ``isOnYouTubeMusic`` metadata.  These are
    the public signals shared by the YouTube Music catalog: Music category,
    Topic/Art Track channels, partner-claimed recordings, VEVO and explicit
    official music uploads.
    """
    if str(category_id or "") != "10":
        return ""
    channel = channel_title or ""
    video_title = title or ""
    if _TOPIC_CHANNEL_RE.search(channel):
        return "art_track"
    if _VEVO_CHANNEL_RE.search(channel):
        return "vevo"
    if bool(licensed_content):
        return "licensed"
    if _OFFICIAL_MUSIC_RE.search(video_title):
        return "official"
    if _OFFICIAL_CHANNEL_RE.search(channel):
        return "official_channel"
    return ""


def is_youtube_music_candidate(item: Dict[str, Any]) -> bool:
    """Whether a Data API result has a reliable YouTube music-catalog signal."""
    return bool(
        item.get("music_origin")
        or youtube_music_origin(
            title=str(item.get("title") or ""),
            channel_title=str(item.get("channel_title") or ""),
            category_id=str(item.get("category_id") or ""),
            licensed_content=bool(item.get("licensed_content")),
        )
    )


def _music_origin_bonus(origin: str) -> float:
    return {
        "art_track": 70.0,
        "vevo": 65.0,
        "licensed": 55.0,
        "official": 45.0,
        "official_channel": 35.0,
    }.get(origin or "", 0.0)


def parse_iso8601_duration(raw: str) -> int:
    if not raw:
        return 0
    match = _ISO8601_DURATION_RE.fullmatch(raw.strip())
    if not match:
        return 0
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def _duration_score(
    video_duration_sec: int, track_duration_ms: Optional[int]
) -> float:
    """Return duration contribution, or -1.0 for hard reject."""
    if track_duration_ms and track_duration_ms > 0 and video_duration_sec > 0:
        track_sec = track_duration_ms / 1000.0
        diff = abs(video_duration_sec - track_sec)
        ratio = diff / track_sec

        # Hard reject: too short/long to be the same track.
        if video_duration_sec < max(45, track_sec * 0.45):
            return -1.0
        if video_duration_sec > track_sec * 1.8 + 90:
            return -1.0
        if ratio > 0.35:
            return -1.0

        if ratio <= 0.08:
            return 100.0
        if ratio <= 0.15:
            return 75.0
        if ratio <= 0.22:
            return 45.0
        if ratio <= 0.30:
            return 15.0
        return -40.0

    if video_duration_sec > 0:
        if 120 <= video_duration_sec <= 420:
            return 20.0
        if video_duration_sec < 60 or video_duration_sec > 900:
            return -1.0
    return 0.0


def score_youtube_candidate(
    title: str,
    *,
    video_duration_sec: int,
    track_duration_ms: Optional[int],
    expected_title: Optional[str] = None,
    expected_artists: Optional[Sequence[str]] = None,
    channel_title: str = "",
    explicit_variant_ok: bool = False,
    category_id: str = "",
    licensed_content: bool = False,
    music_origin: str = "",
) -> float:
    """Score a YouTube candidate.

    Hard rejects (``-1``):
    - duration incompatible
    - title similarity too weak (when expected_title provided)
    - artist incompatible (when artists provided)
    - bad-variant titles unless catalog explicitly requests that variant

    Soft penalties: live/cover/karaoke/nightcore/... when not explicit.
    Soft bonuses: Official Audio/Video, title/artist match, duration.
    """
    title = title or ""
    if not title.strip():
        return -1.0

    expected = expected_title or ""
    artists = list(expected_artists or [])
    meta = normalize_track_meta(expected, " ".join(artists)) if expected else None
    expect_core = (
        strip_title_noise(expected) or expected if expected else ""
    )
    if meta and meta.artists and not artists:
        artists = list(meta.artists)

    # Duration hard gate.
    dur = _duration_score(video_duration_sec, track_duration_ms)
    if dur < 0:
        return -1.0

    # Title similarity hard gate (weak titles never auto-accept).
    sim = title_similarity(title, expect_core or title) if expect_core else 0.5
    if expect_core and sim < _MIN_TITLE_SIM:
        return -1.0

    # Artist match using title + channel.
    artist_hay = f"{title} {channel_title}"
    a_score = artist_match_score(artist_hay, artists) if artists else 0.5
    if artists and a_score < _MIN_ARTIST_SCORE:
        return -1.0

    score = 0.0
    score += dur
    score += sim * 55.0
    score += a_score * 40.0

    if _GOOD_TITLE_RE.search(title) or _GOOD_TITLE_RE.search(channel_title):
        score += 40.0

    origin = music_origin or youtube_music_origin(
        title=title,
        channel_title=channel_title,
        category_id=category_id,
        licensed_content=licensed_content,
    )
    score += _music_origin_bonus(origin)

    bad = _BAD_TITLE_RE.search(title)
    if bad:
        token = (bad.group(1) or "").casefold()
        catalog_wants = bool(
            expect_core
            and _EXPLICIT_VARIANT_RE.search(expect_core)
            and any(
                w in (expect_core or "").casefold()
                for w in (token, token.split()[0] if token else "")
                if w
            )
        )
        if explicit_variant_ok or catalog_wants:
            # Soft penalty only — variant was requested by catalog/query.
            score -= 20.0
        else:
            # Never auto-accept cover/live/karaoke/clip/... unless requested.
            return -1.0

    return score


def pick_best_youtube_candidate(
    candidates: List[Dict[str, Any]],
    track_duration_ms: Optional[int],
    *,
    expected_title: Optional[str] = None,
    expected_artists: Optional[Sequence[str]] = None,
) -> Optional[str]:
    picked = pick_best_youtube_candidate_detailed(
        candidates,
        track_duration_ms,
        expected_title=expected_title,
        expected_artists=expected_artists,
    )
    return picked["video_id"] if picked else None


def pick_best_youtube_candidate_detailed(
    candidates: List[Dict[str, Any]],
    track_duration_ms: Optional[int],
    *,
    expected_title: Optional[str] = None,
    expected_artists: Optional[Sequence[str]] = None,
    min_accept_score: Optional[float] = None,
    allow_secondary_variants: bool = False,
) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_score = -1.0
    threshold = _MIN_ACCEPT_SCORE if min_accept_score is None else float(min_accept_score)

    for item in candidates:
        video_id = item.get("video_id")
        if not video_id:
            continue
        # Explicit unavailable / private markers when provided by callers.
        status = (item.get("availability") or item.get("status") or "").lower()
        if status in ("unavailable", "private", "deleted", "blocked"):
            continue

        score = score_youtube_candidate(
            item.get("title", ""),
            video_duration_sec=int(item.get("duration_sec") or 0),
            track_duration_ms=track_duration_ms,
            expected_title=expected_title,
            expected_artists=expected_artists,
            channel_title=item.get("channel_title") or item.get("uploader") or "",
            explicit_variant_ok=allow_secondary_variants,
            category_id=str(item.get("category_id") or ""),
            licensed_content=bool(item.get("licensed_content")),
            music_origin=str(item.get("music_origin") or ""),
        )
        if score < 0 or score < threshold:
            continue
        if score > best_score:
            best_score = score
            best = {
                **item,
                "video_id": video_id,
                "_score": score,
                "confidence_score": round(min(0.99, score / 200.0), 3),
            }

    return best
