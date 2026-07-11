"""YouTube search query + candidate scoring."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

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
    r"tik[\s-]?tok|shorts"
    r")\b",
    re.IGNORECASE,
)

_GOOD_TITLE_RE = re.compile(
    r"\b(official(?: audio| video| music video| mv| visualizer)?|"
    r"provided to youtube|vevo)\b",
    re.IGNORECASE,
)

_ISO8601_DURATION_RE = re.compile(
    r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def build_search_query(track_name: str, artist_name: str) -> str:
    artist = artist_name.strip()
    if artist:
        return f"{track_name} {artist} official audio"
    return f"{track_name} official audio"


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


def score_youtube_candidate(
    title: str,
    *,
    video_duration_sec: int,
    track_duration_ms: Optional[int],
) -> float:
    title = title or ""
    if _BAD_TITLE_RE.search(title):
        return -1.0

    score = 0.0
    if _GOOD_TITLE_RE.search(title):
        score += 40.0

    if track_duration_ms and track_duration_ms > 0 and video_duration_sec > 0:
        track_sec = track_duration_ms / 1000.0
        diff = abs(video_duration_sec - track_sec)
        ratio = diff / track_sec

        if ratio <= 0.08:
            score += 100.0
        elif ratio <= 0.15:
            score += 75.0
        elif ratio <= 0.22:
            score += 45.0
        elif ratio <= 0.30:
            score += 15.0
        else:
            score -= 40.0

        if video_duration_sec < max(45, track_sec * 0.45):
            return -1.0
        if video_duration_sec > track_sec * 1.8 + 90:
            return -1.0
    elif video_duration_sec > 0:
        if 120 <= video_duration_sec <= 420:
            score += 20.0
        elif video_duration_sec < 60 or video_duration_sec > 900:
            return -1.0

    return score


def pick_best_youtube_candidate(
    candidates: List[Dict[str, Any]],
    track_duration_ms: Optional[int],
) -> Optional[str]:
    best_id: Optional[str] = None
    best_score = -1.0

    for item in candidates:
        video_id = item.get("video_id")
        if not video_id:
            continue
        score = score_youtube_candidate(
            item.get("title", ""),
            video_duration_sec=int(item.get("duration_sec") or 0),
            track_duration_ms=track_duration_ms,
        )
        if score < 0:
            continue
        if score > best_score:
            best_score = score
            best_id = video_id

    return best_id
