# -*- coding: utf-8 -*-
"""YouTube audio provider — official Data API only (IFrame playback on FE).

Does not download, extract stream URLs, or use yt-dlp/scraping.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import get_settings

from .base import AudioProvider
from .cache import STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK
from .metadata_normalize import build_search_query_variants, normalize_track_meta
from .models import ResolvedSource, TrackContext
from .youtube_scoring import (
    build_search_query,
    parse_iso8601_duration,
    pick_best_youtube_candidate_detailed,
    score_youtube_candidate,
)

logger = logging.getLogger(__name__)

_YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_REQUEST_TIMEOUT = float(get_settings().audio_provider_timeout_sec or 12.0)
_SEARCH_MAX_RESULTS = 12
_MAX_QUERY_ATTEMPTS = 5


class YouTubeProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "youtube"

    def resolve(self, track: TrackContext) -> ResolvedSource:
        meta = normalize_track_meta(track.track_name, track.artist_name)
        queries = build_search_query_variants(
            track.track_name, track.artist_name, max_variants=_MAX_QUERY_ATTEMPTS
        )
        if not queries:
            queries = [build_search_query(track.track_name, track.artist_name)]

        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=queries[0] if queries else "",
            )

        last_outcome = STATUS_NOT_FOUND
        last_query = queries[0]
        artists = list(meta.artists)

        for query in queries:
            last_query = query
            video, outcome = self._resolve_video(
                query,
                api_key,
                track.duration_ms,
                expected_title=meta.original_title or track.track_name,
                expected_artists=artists,
            )
            last_outcome = outcome
            if outcome == STATUS_OK and video:
                return ResolvedSource(
                    track_id=track.track_id,
                    provider=self.name,
                    status=STATUS_OK,
                    source_ref=video["video_id"],
                    youtube_video_id=video["video_id"],
                    query=query,
                    confidence_score=video.get("confidence_score"),
                )
            if outcome == STATUS_ERROR:
                continue

        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=last_outcome if last_outcome != STATUS_OK else STATUS_NOT_FOUND,
            query=last_query,
        )

    def search_candidates(
        self,
        track: TrackContext,
        *,
        max_queries: int = 2,
        max_results: int = 8,
    ) -> List[Dict[str, Any]]:
        """Return ranked candidate dicts without writing cache (Data API only)."""
        meta = normalize_track_meta(track.track_name, track.artist_name)
        queries = build_search_query_variants(
            track.track_name, track.artist_name, max_variants=max_queries
        )
        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            return []
        seen: set[str] = set()
        ranked: List[Dict[str, Any]] = []

        for query in queries:
            raw = self._collect_candidates(query, api_key)
            for item in raw:
                vid = item.get("video_id")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                score = score_youtube_candidate(
                    item.get("title", ""),
                    video_duration_sec=int(item.get("duration_sec") or 0),
                    track_duration_ms=track.duration_ms,
                    expected_title=meta.original_title,
                    expected_artists=list(meta.artists),
                    channel_title=item.get("channel_title") or "",
                )
                ranked.append(
                    {
                        **item,
                        "query": query,
                        "score": score,
                        "accepted": score >= 0,
                    }
                )

        ranked.sort(key=lambda c: c.get("score") or -999, reverse=True)
        return ranked[:max_results]

    def search_query_candidates(
        self,
        query: str,
        *,
        max_results: int = 8,
        expected_title: str = "",
        expected_artists: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Free-text YouTube search for music fallback (5–10 options)."""
        api_key = get_settings().youtube_api_key.strip()
        if not api_key or not (query or "").strip():
            return []
        raw = self._collect_candidates(query.strip(), api_key)
        artists = list(expected_artists or [])
        ranked: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw:
            vid = item.get("video_id")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            score = score_youtube_candidate(
                item.get("title", ""),
                video_duration_sec=int(item.get("duration_sec") or 0),
                track_duration_ms=None,
                expected_title=expected_title or query,
                expected_artists=artists,
                channel_title=item.get("channel_title") or "",
            )
            ranked.append({**item, "query": query, "score": score, "origin": "youtube"})
        ranked.sort(key=lambda c: c.get("score") or -999, reverse=True)
        return ranked[: max(5, min(int(max_results), 10))]

    def _resolve_video(
        self,
        query: str,
        api_key: str,
        track_duration_ms: Optional[int],
        *,
        expected_title: str,
        expected_artists: List[str],
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        api_video, api_ok = self._search_api(
            query,
            api_key,
            track_duration_ms,
            expected_title=expected_title,
            expected_artists=expected_artists,
        )
        if not api_ok:
            return None, STATUS_ERROR
        return api_video, STATUS_OK if api_video else STATUS_NOT_FOUND

    def _collect_candidates(self, query: str, api_key: str) -> List[Dict[str, Any]]:
        api_raw, api_ok = self._search_api_raw(query, api_key)
        if api_ok and api_raw:
            return api_raw
        return []

    def _search_api(
        self,
        query: str,
        api_key: str,
        track_duration_ms: Optional[int],
        *,
        expected_title: str,
        expected_artists: List[str],
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        candidates, ok = self._search_api_raw(query, api_key)
        if not ok:
            return None, False
        if not candidates:
            return None, True
        return (
            pick_best_youtube_candidate_detailed(
                candidates,
                track_duration_ms,
                expected_title=expected_title,
                expected_artists=expected_artists,
            ),
            True,
        )

    def _search_api_raw(
        self, query: str, api_key: str
    ) -> Tuple[List[Dict[str, Any]], bool]:
        params = {
            "key": api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "videoSyndicated": "true",
            "videoCategoryId": "10",
            "maxResults": str(_SEARCH_MAX_RESULTS),
        }
        try:
            resp = httpx.get(_YT_SEARCH_URL, params=params, timeout=_REQUEST_TIMEOUT)
        except httpx.HTTPError as exc:
            logger.warning("YouTube search failed: %s", exc)
            return [], False

        if resp.status_code == 403:
            logger.warning("YouTube quota or auth rejected search")
            return [], False
        if resp.status_code != 200:
            logger.warning("YouTube search returned %s", resp.status_code)
            return [], False

        items = resp.json().get("items") or []
        video_ids = [
            item.get("id", {}).get("videoId")
            for item in items
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return [], True

        details = self._fetch_video_details(video_ids, api_key)
        if details is None:
            return [], False
        return [details[vid] for vid in video_ids if vid in details], True

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
                    "part": "contentDetails,snippet,status",
                },
                timeout=_REQUEST_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            logger.warning("YouTube videos.list failed: %s", exc)
            return None
        if resp.status_code != 200:
            return None

        out: Dict[str, Dict[str, Any]] = {}
        for item in resp.json().get("items") or []:
            vid = item.get("id")
            if not vid:
                continue
            snippet = item.get("snippet") or {}
            status = item.get("status") or {}
            details = item.get("contentDetails") or {}
            if status.get("privacyStatus") not in (None, "public", "unlisted"):
                continue
            if status.get("embeddable") is False:
                continue
            duration_sec = parse_iso8601_duration(details.get("duration") or "")
            thumbs = snippet.get("thumbnails") or {}
            thumb = (
                (thumbs.get("high") or {}).get("url")
                or (thumbs.get("medium") or {}).get("url")
                or (thumbs.get("default") or {}).get("url")
                or ""
            )
            out[vid] = {
                "video_id": vid,
                "title": snippet.get("title") or "",
                "channel_title": snippet.get("channelTitle") or "",
                "channel_id": snippet.get("channelId") or "",
                "duration_sec": duration_sec,
                "thumbnail": thumb,
                "published_at": snippet.get("publishedAt") or "",
                "embeddable": bool(status.get("embeddable", True)),
            }
        return out
