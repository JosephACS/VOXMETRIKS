"""Resolve real playback sources (YouTube video ids) for catalog tracks.

We never download or re-host audio. We resolve the matching YouTube video id
for a real track and let the frontend play it through the official YouTube
IFrame player (full-length, free, ToS-compliant). Results are cached in the
``app_track_audio_source`` DuckDB table so each track is
searched only once.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

import duckdb
import httpx

from app.core.config import get_settings
from app.core.database import using_write_conn
from app.core.time_util import utc_now

logger = logging.getLogger(__name__)

_YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_REQUEST_TIMEOUT = 8.0
_SEARCH_MAX_RESULTS = 12

# status values stored in app_track_audio_source.status
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_DISABLED = "disabled"  # no API key configured
STATUS_ERROR = "error"  # transient API/quota failure — NOT cached, retried later
STATUS_PENDING = "pending"  # resolution scheduled in background

_scheduled_lock = threading.Lock()
_scheduled_ids: set[int] = set()

# Reject obvious non-studio matches (covers, lyric videos, loops, etc.)
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


def parse_iso8601_duration(raw: str) -> int:
    """Parse YouTube ``contentDetails.duration`` (ISO-8601) → seconds."""
    if not raw:
        return 0
    match = _ISO8601_DURATION_RE.fullmatch(raw.strip())
    if not match:
        return 0
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def _track_info(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Tuple[str, str, Optional[int]]]:
    """Return ``(track_name, artist_name, duration_ms)`` or ``None``."""
    row = conn.execute(
        """
        SELECT dt.nombre_track, da.nombre_artista, dt.duration_ms
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track = ?
        """,
        [track_id],
    ).fetchone()
    if not row:
        return None
    track_name = (row[0] or "").strip()
    artist_name = (row[1] or "").strip()
    duration_ms = int(row[2]) if row[2] is not None else None
    if not track_name:
        return None
    return track_name, artist_name, duration_ms


def _build_search_query(track_name: str, artist_name: str) -> str:
    """Search query biased toward the original studio recording."""
    artist = artist_name.strip()
    if artist:
        return f"{track_name} {artist} official audio"
    return f"{track_name} official audio"


def score_youtube_candidate(
    title: str,
    *,
    video_duration_sec: int,
    track_duration_ms: Optional[int],
) -> float:
    """Higher is better. Negative → discard."""
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

        # Duration is the strongest signal against covers / loops / live jams.
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

        # Hard rejects: 30s preview-ish or hour-long loops for a ~3–4 min song.
        if video_duration_sec < max(45, track_sec * 0.45):
            return -1.0
        if video_duration_sec > track_sec * 1.8 + 90:
            return -1.0
    elif video_duration_sec > 0:
        # No catalog duration → mild preference for typical single length.
        if 120 <= video_duration_sec <= 420:
            score += 20.0
        elif video_duration_sec < 60 or video_duration_sec > 900:
            return -1.0

    return score


def pick_best_youtube_candidate(
    candidates: List[Dict[str, Any]],
    track_duration_ms: Optional[int],
) -> Optional[str]:
    """Pick the best ``videoId`` from scored search results."""
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


def _read_cache(conn: duckdb.DuckDBPyConnection, track_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT track_id, provider, youtube_video_id, query, status
        FROM app_track_audio_source
        WHERE track_id = ?
        """,
        [track_id],
    ).fetchone()
    if not row:
        return None
    return {
        "track_id": int(row[0]),
        "provider": row[1],
        "youtube_video_id": row[2],
        "query": row[3],
        "status": row[4],
    }


def _write_cache(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    youtube_video_id: Optional[str],
    query: Optional[str],
    status: str,
) -> None:
    conn.execute("DELETE FROM app_track_audio_source WHERE track_id = ?", [track_id])
    conn.execute(
        """
        INSERT INTO app_track_audio_source
            (track_id, provider, youtube_video_id, query, status, resolved_at)
        VALUES (?, 'youtube', ?, ?, ?, ?)
        """,
        [track_id, youtube_video_id, query, status, utc_now()],
    )


def _fetch_video_details(
    video_ids: List[str], api_key: str
) -> Optional[Dict[str, Dict[str, Any]]]:
    """Batch-fetch title + duration for candidate videos.

    Returns ``None`` on a transient API/quota failure (so the caller can avoid
    caching a false ``not_found``), or a (possibly empty) dict on success.
    """
    if not video_ids:
        return {}
    try:
        resp = httpx.get(
            _YT_VIDEOS_URL,
            params={
                "key": api_key,
                "id": ",".join(video_ids),
                "part": "contentDetails,snippet",
            },
            timeout=_REQUEST_TIMEOUT,
        )
    except httpx.HTTPError as exc:
        logger.warning("YouTube videos.list failed: %s", exc)
        return None

    if resp.status_code != 200:
        logger.warning(
            "YouTube videos.list returned %s: %s", resp.status_code, resp.text[:200]
        )
        return None

    out: Dict[str, Dict[str, Any]] = {}
    for item in resp.json().get("items") or []:
        vid = item.get("id")
        if not vid:
            continue
        snippet = item.get("snippet") or {}
        details = item.get("contentDetails") or {}
        out[vid] = {
            "video_id": vid,
            "title": snippet.get("title") or "",
            "duration_sec": parse_iso8601_duration(details.get("duration") or ""),
        }
    return out


def _search_youtube(
    query: str,
    api_key: str,
    track_duration_ms: Optional[int],
) -> Tuple[Optional[str], bool]:
    """Resolve the best embeddable YouTube video id for the query.

    Returns ``(video_id, api_ok)``. ``api_ok`` is ``False`` when the API call
    itself failed (network error, quota exceeded, non-200) so the caller can
    avoid caching a false ``not_found`` and retry later.
    """
    params = {
        "key": api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "videoEmbeddable": "true",
        "videoCategoryId": "10",  # Music
        "maxResults": str(_SEARCH_MAX_RESULTS),
    }
    try:
        resp = httpx.get(_YT_SEARCH_URL, params=params, timeout=_REQUEST_TIMEOUT)
    except httpx.HTTPError as exc:
        logger.warning("YouTube search request failed: %s", exc)
        return None, False

    if resp.status_code != 200:
        logger.warning(
            "YouTube search returned %s: %s", resp.status_code, resp.text[:200]
        )
        return None, False

    items = resp.json().get("items") or []
    video_ids = [
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return None, True  # API worked, but genuinely nothing matched

    details = _fetch_video_details(video_ids, api_key)
    if details is None:
        return None, False  # transient failure on videos.list
    candidates = [details[vid] for vid in video_ids if vid in details]
    return pick_best_youtube_candidate(candidates, track_duration_ms), True


def _search_youtube_ytdlp(
    query: str,
    track_duration_ms: Optional[int],
) -> Tuple[Optional[str], bool]:
    """Search YouTube via yt-dlp (no Google Cloud quota).

    Returns ``(video_id, search_ok)``. ``search_ok`` is ``False`` only on a
    transient failure (network, yt-dlp missing, rate limit).
    """
    try:
        import yt_dlp
    except ImportError:
        logger.warning("yt-dlp not installed — pip install yt-dlp")
        return None, False

    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "socket_timeout": _REQUEST_TIMEOUT,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"ytsearch{_SEARCH_MAX_RESULTS}:{query}",
                download=False,
            )
    except Exception as exc:
        logger.warning("yt-dlp search failed for %r: %s", query, exc)
        return None, False

    entries = info.get("entries") if isinstance(info, dict) else None
    if not entries:
        return None, True

    candidates: List[Dict[str, Any]] = []
    for item in entries:
        if not item:
            continue
        video_id = item.get("id")
        if not video_id:
            continue
        candidates.append(
            {
                "video_id": video_id,
                "title": item.get("title") or "",
                "duration_sec": int(item.get("duration") or 0),
            }
        )
    return pick_best_youtube_candidate(candidates, track_duration_ms), True


def _resolve_video_id(
    query: str,
    api_key: str,
    track_duration_ms: Optional[int],
) -> Tuple[Optional[str], str]:
    """Pick the best YouTube video id — yt-dlp first (no quota), API as backup.

    Returns ``(video_id, outcome)`` where ``outcome`` is one of
    ``STATUS_OK``, ``STATUS_NOT_FOUND``, or ``STATUS_ERROR``.
    """
    video_id, ytdlp_ok = _search_youtube_ytdlp(query, track_duration_ms)
    if ytdlp_ok and video_id:
        return video_id, STATUS_OK
    if ytdlp_ok and not video_id:
        # yt-dlp searched successfully but found no acceptable match.
        if api_key:
            api_id, api_ok = _search_youtube(query, api_key, track_duration_ms)
            if api_ok:
                return api_id, STATUS_OK if api_id else STATUS_NOT_FOUND
        return None, STATUS_NOT_FOUND

    # yt-dlp failed transiently — try API if available, else error.
    if api_key:
        api_id, api_ok = _search_youtube(query, api_key, track_duration_ms)
        if api_ok:
            return api_id, STATUS_OK if api_id else STATUS_NOT_FOUND

    return None, STATUS_ERROR


def _schedule_resolve(track_id: int) -> None:
    with _scheduled_lock:
        if track_id in _scheduled_ids:
            return
        _scheduled_ids.add(track_id)

    def _job() -> None:
        try:
            with using_write_conn() as conn:
                resolve_audio_source(conn, track_id, force=False)
        finally:
            with _scheduled_lock:
                _scheduled_ids.discard(track_id)

    threading.Thread(target=_job, daemon=True, name=f"audio-resolve-{track_id}").start()


def get_audio_source_response(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
    async_resolve: bool = True,
) -> Optional[Dict[str, Any]]:
    """Return cached audio source or schedule background resolution on miss."""
    info = _track_info(conn, track_id)
    if info is None:
        return None
    track_name, artist_name, duration_ms = info
    query = _build_search_query(track_name, artist_name)

    if not force:
        cached = _read_cache(conn, track_id)
        if cached and cached["status"] in (STATUS_OK, STATUS_NOT_FOUND, STATUS_DISABLED):
            return cached

    # yt-dlp resolves without an API key; only cache "disabled" when both paths
    # are unavailable (handled inside resolve_audio_source on sync resolve).
    if async_resolve and not force:
        _schedule_resolve(track_id)
        return {
            "track_id": track_id,
            "provider": "youtube",
            "youtube_video_id": None,
            "query": query,
            "status": STATUS_PENDING,
        }

    with using_write_conn() as write_conn:
        return resolve_audio_source(write_conn, track_id, force=force)


def resolve_audio_source(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """Resolve (and cache) the YouTube video id for a track.

    Returns a dict ``{track_id, provider, youtube_video_id, status, query}``
    or ``None`` if the track does not exist. When no API key is configured the
    status is ``disabled`` so the frontend can fall back to demo audio.
    """
    info = _track_info(conn, track_id)
    if info is None:
        return None
    track_name, artist_name, duration_ms = info
    query = _build_search_query(track_name, artist_name)

    if not force:
        cached = _read_cache(conn, track_id)
        if cached and cached["status"] in (STATUS_OK, STATUS_NOT_FOUND):
            return cached

    api_key = get_settings().youtube_api_key.strip()
    video_id, outcome = _resolve_video_id(query, api_key, duration_ms)

    if outcome == STATUS_ERROR:
        return {
            "track_id": track_id,
            "provider": "youtube",
            "youtube_video_id": None,
            "query": query,
            "status": STATUS_ERROR,
        }

    status = outcome
    _write_cache(conn, track_id, video_id, query, status)
    return {
        "track_id": track_id,
        "provider": "youtube",
        "youtube_video_id": video_id,
        "query": query,
        "status": status,
    }
