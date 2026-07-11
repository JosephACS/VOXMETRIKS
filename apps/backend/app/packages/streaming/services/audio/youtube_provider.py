"""YouTube audio provider (yt-dlp primary, Data API backup)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import get_settings

from .youtube_scoring import (
    build_search_query,
    parse_iso8601_duration,
    pick_best_youtube_candidate,
    score_youtube_candidate,
)
from .base import AudioProvider
from .cache import STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK
from .models import ResolvedSource, TrackContext

logger = logging.getLogger(__name__)

_YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_REQUEST_TIMEOUT = 8.0
_SEARCH_MAX_RESULTS = 12


class YouTubeProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "youtube"

    def resolve(self, track: TrackContext) -> ResolvedSource:
        query = build_search_query(track.track_name, track.artist_name)
        api_key = get_settings().youtube_api_key.strip()
        video_id, outcome = self._resolve_video_id(query, api_key, track.duration_ms)
        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=outcome,
            source_ref=video_id,
            youtube_video_id=video_id,
            query=query,
            confidence_score=0.85 if video_id else None,
        )

    def _resolve_video_id(
        self, query: str, api_key: str, track_duration_ms: Optional[int]
    ) -> Tuple[Optional[str], str]:
        video_id, ytdlp_ok = self._search_ytdlp(query, track_duration_ms)
        if ytdlp_ok and video_id:
            return video_id, STATUS_OK
        if ytdlp_ok and not video_id:
            if api_key:
                api_id, api_ok = self._search_api(query, api_key, track_duration_ms)
                if api_ok:
                    return api_id, STATUS_OK if api_id else STATUS_NOT_FOUND
            return None, STATUS_NOT_FOUND
        if api_key:
            api_id, api_ok = self._search_api(query, api_key, track_duration_ms)
            if api_ok:
                return api_id, STATUS_OK if api_id else STATUS_NOT_FOUND
        return None, STATUS_ERROR

    def _search_ytdlp(
        self, query: str, track_duration_ms: Optional[int]
    ) -> Tuple[Optional[str], bool]:
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt-dlp not installed")
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

    def _search_api(
        self, query: str, api_key: str, track_duration_ms: Optional[int]
    ) -> Tuple[Optional[str], bool]:
        params = {
            "key": api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "videoCategoryId": "10",
            "maxResults": str(_SEARCH_MAX_RESULTS),
        }
        try:
            resp = httpx.get(_YT_SEARCH_URL, params=params, timeout=_REQUEST_TIMEOUT)
        except httpx.HTTPError as exc:
            logger.warning("YouTube search failed: %s", exc)
            return None, False

        if resp.status_code != 200:
            logger.warning("YouTube search returned %s", resp.status_code)
            return None, False

        items = resp.json().get("items") or []
        video_ids = [
            item.get("id", {}).get("videoId")
            for item in items
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return None, True

        details = self._fetch_video_details(video_ids, api_key)
        if details is None:
            return None, False
        candidates = [details[vid] for vid in video_ids if vid in details]
        return pick_best_youtube_candidate(candidates, track_duration_ms), True

    def _fetch_video_details(
        self, video_ids: List[str], api_key: str
    ) -> Optional[Dict[str, Dict[str, Any]]]:
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
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None

        from .youtube_scoring import parse_iso8601_duration

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
