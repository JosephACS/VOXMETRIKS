# -*- coding: utf-8 -*-
"""YouTube audio provider — official Data API only (IFrame playback on FE).

Does not download, extract stream URLs, or use yt-dlp/scraping.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import get_settings

from .base import AudioProvider
from .cache import STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK
from .metadata_normalize import (
    build_search_query_variants,
    normalize_track_meta,
    strip_title_noise,
)
from .models import ResolvedSource, TrackContext
from .youtube_scoring import (
    build_search_query,
    is_youtube_music_candidate,
    parse_iso8601_duration,
    pick_best_youtube_candidate_detailed,
    score_youtube_candidate,
    youtube_music_origin,
)

logger = logging.getLogger(__name__)

_YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_REQUEST_TIMEOUT = float(get_settings().audio_provider_timeout_sec or 12.0)
_SEARCH_MAX_RESULTS = 12
_MAX_QUERY_ATTEMPTS = 5
# Ranked YouTube video ids remembered from the last successful search per track.
# Used for exclude/fallback without a second Data API round-trip (avoids 429 flake).
_ALTERNATE_IDS: Dict[int, List[str]] = {}
_ALT_MAX = 8


def _remember_alternate_ids(track_id: int, ranked_ids: List[str], chosen_id: Optional[str]) -> None:
    ordered: List[str] = []
    for vid in ranked_ids:
        if not vid or vid == chosen_id or vid in ordered:
            continue
        ordered.append(vid)
        if len(ordered) >= _ALT_MAX:
            break
    if ordered:
        _ALTERNATE_IDS[track_id] = ordered


def _next_remembered_alternate(track_id: int, exclude_ids: set[str]) -> Optional[str]:
    for vid in _ALTERNATE_IDS.get(track_id) or ():
        if vid not in exclude_ids:
            return vid
    return None


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

        # Prefer cleaned-title queries first (drop "sped up" / "with …" noise) so
        # recovery can land on an embeddable official upload instead of edit uploads.
        core = strip_title_noise(track.track_name)
        if core and core.casefold() != (track.track_name or "").casefold():
            preferred = [
                q
                for q in queries
                if "sped" not in q.casefold()
                and "slowed" not in q.casefold()
                and "nightcore" not in q.casefold()
            ]
            rest = [q for q in queries if q not in preferred]
            if preferred:
                queries = preferred + rest

        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=queries[0] if queries else "",
            )

        exclude_ids = set(track.exclude_source_refs or ())
        # Prefer a previously ranked alternate — no extra YouTube search.
        if exclude_ids:
            alt = _next_remembered_alternate(track.track_id, exclude_ids)
            if alt:
                return ResolvedSource(
                    track_id=track.track_id,
                    provider=self.name,
                    status=STATUS_OK,
                    source_ref=alt,
                    youtube_video_id=alt,
                    query=queries[0],
                    confidence_score=0.5,
                )

        last_outcome = STATUS_NOT_FOUND
        last_query = queries[0]
        artists = list(meta.artists)
        # When excluding a failed embed, retry search briefly — Data API 429 is common.
        attempts = 3 if exclude_ids else 1

        for attempt in range(attempts):
            for query in queries:
                last_query = query
                video, outcome, ranked_ids = self._resolve_video(
                    query,
                    api_key,
                    track.duration_ms,
                    expected_title=meta.original_title or track.track_name,
                    expected_artists=artists,
                    exclude_ids=exclude_ids,
                )
                last_outcome = outcome
                if outcome == STATUS_OK and video:
                    _remember_alternate_ids(
                        track.track_id, ranked_ids, video.get("video_id")
                    )
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
            if attempt + 1 < attempts and last_outcome in (STATUS_ERROR, STATUS_NOT_FOUND):
                time.sleep(0.35 * (attempt + 1))
                continue
            break

        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=last_outcome if last_outcome != STATUS_OK else STATUS_NOT_FOUND,
            query=last_query,
        )

    def warm_alternates(self, track: TrackContext) -> List[str]:
        """Search once and remember ranked video ids for later exclude recovery."""
        api_key = get_settings().youtube_api_key.strip()
        if not api_key:
            return list(_ALTERNATE_IDS.get(track.track_id) or ())
        meta = normalize_track_meta(track.track_name, track.artist_name)
        queries = build_search_query_variants(
            track.track_name, track.artist_name, max_variants=2
        )
        if not queries:
            queries = [build_search_query(track.track_name, track.artist_name)]
        artists = list(meta.artists)
        for query in queries:
            _video, outcome, ranked_ids = self._resolve_video(
                query,
                api_key,
                track.duration_ms,
                expected_title=meta.original_title or track.track_name,
                expected_artists=artists,
                exclude_ids=None,
            )
            if ranked_ids:
                _ALTERNATE_IDS[track.track_id] = ranked_ids[:_ALT_MAX]
                return _ALTERNATE_IDS[track.track_id]
            if outcome == STATUS_ERROR:
                continue
        return list(_ALTERNATE_IDS.get(track.track_id) or ())

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
                if track.exclude_source_refs and vid in track.exclude_source_refs:
                    continue
                seen.add(vid)
                score = score_youtube_candidate(
                    item.get("title", ""),
                    video_duration_sec=int(item.get("duration_sec") or 0),
                    track_duration_ms=track.duration_ms,
                    expected_title=meta.original_title,
                    expected_artists=list(meta.artists),
                    channel_title=item.get("channel_title") or "",
                    category_id=str(item.get("category_id") or ""),
                    licensed_content=bool(item.get("licensed_content")),
                    music_origin=str(item.get("music_origin") or ""),
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
        if ranked:
            _remember_alternate_ids(
                track.track_id,
                [str(c["video_id"]) for c in ranked if c.get("video_id")],
                None,
            )
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
        # When the query is entirely external we do not yet know which words
        # belong to the title and which belong to the artist. YouTube relevance
        # plus the music-catalog signals remain the identity gate; applying the
        # whole free-text query as a strict title would reject valid official
        # results such as "song + artist" searches.
        score_title = (expected_title or query) if artists else ""
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
                expected_title=score_title,
                expected_artists=artists,
                channel_title=item.get("channel_title") or "",
                category_id=str(item.get("category_id") or ""),
                licensed_content=bool(item.get("licensed_content")),
                music_origin=str(item.get("music_origin") or ""),
            )
            # Free-text discovery is intentionally stricter than resolver
            # recovery: do not show clips, covers, fan lyrics or mismatched
            # variants merely because Content ID marked them as licensed.
            if score < 0:
                continue
            ranked.append(
                {
                    **item,
                    "query": query,
                    "score": score,
                    "origin": "youtube",
                    "accepted": True,
                }
            )
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
        exclude_ids: Optional[set[str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
        api_video, api_ok, ranked_ids = self._search_api(
            query,
            api_key,
            track_duration_ms,
            expected_title=expected_title,
            expected_artists=expected_artists,
            exclude_ids=exclude_ids,
        )
        if not api_ok:
            return None, STATUS_ERROR, ranked_ids
        return api_video, (STATUS_OK if api_video else STATUS_NOT_FOUND), ranked_ids

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
        exclude_ids: Optional[set[str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], bool, List[str]]:
        candidates, ok = self._search_api_raw(query, api_key)
        if not ok:
            return None, False, []
        ranked_ids = self._rank_candidate_ids(
            candidates,
            track_duration_ms,
            expected_title=expected_title,
            expected_artists=expected_artists,
        )
        if exclude_ids:
            candidates = [c for c in candidates if c.get("video_id") not in exclude_ids]
        if not candidates:
            return None, True, ranked_ids
        picked = pick_best_youtube_candidate_detailed(
            candidates,
            track_duration_ms,
            expected_title=expected_title,
            expected_artists=expected_artists,
        )
        # A catalog match can legitimately be published as a lyrics/visualizer
        # upload (for example "Ik Tera"). Keep the strict official/plain pass
        # first, then accept a secondary variant only when title, artist and
        # duration still identify the same recording.
        if picked is None:
            picked = pick_best_youtube_candidate_detailed(
                candidates,
                track_duration_ms,
                expected_title=expected_title,
                expected_artists=expected_artists,
                min_accept_score=0.0,
                # A matching lyrics/visualizer upload is better than declaring
                # the song unavailable. Artist/title/duration gates still apply.
                allow_secondary_variants=True,
            )
        return picked, True, ranked_ids

    @staticmethod
    def _rank_candidate_ids(
        candidates: List[Dict[str, Any]],
        track_duration_ms: Optional[int],
        *,
        expected_title: str,
        expected_artists: List[str],
    ) -> List[str]:
        scored: List[Tuple[float, str]] = []
        for item in candidates:
            vid = item.get("video_id")
            if not vid:
                continue
            score = score_youtube_candidate(
                item.get("title", ""),
                video_duration_sec=int(item.get("duration_sec") or 0),
                track_duration_ms=track_duration_ms,
                expected_title=expected_title,
                expected_artists=expected_artists,
                channel_title=item.get("channel_title") or item.get("uploader") or "",
                category_id=str(item.get("category_id") or ""),
                licensed_content=bool(item.get("licensed_content")),
                music_origin=str(item.get("music_origin") or ""),
            )
            if score < 0:
                continue
            scored.append((float(score), str(vid)))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [vid for _, vid in scored]

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
        candidates = [details[vid] for vid in video_ids if vid in details]
        # Keep the discovery surface aligned with the YouTube Music catalog:
        # Topic/Art Tracks, partner-licensed recordings and official uploads.
        return [item for item in candidates if is_youtube_music_candidate(item)], True

    def _fetch_video_details(
        self, video_ids: List[str], api_key: str
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        if not video_ids:
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        # videos.list accepts at most 50 ids. Chunking keeps maintenance jobs
        # correct when revalidating the complete playable catalog at once.
        for start in range(0, len(video_ids), 50):
            batch = video_ids[start : start + 50]
            try:
                resp = httpx.get(
                    _YT_VIDEOS_URL,
                    params={
                        "key": api_key,
                        "id": ",".join(batch),
                        "part": "contentDetails,snippet,status",
                    },
                    timeout=_REQUEST_TIMEOUT,
                )
            except httpx.HTTPError as exc:
                logger.warning("YouTube videos.list failed: %s", exc)
                return None
            if resp.status_code != 200:
                return None

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
                category_id = str(snippet.get("categoryId") or "")
                licensed_content = bool(details.get("licensedContent"))
                origin = youtube_music_origin(
                    title=snippet.get("title") or "",
                    channel_title=snippet.get("channelTitle") or "",
                    category_id=category_id,
                    licensed_content=licensed_content,
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
                    "category_id": category_id,
                    "licensed_content": licensed_content,
                    "music_origin": origin,
                }
        return out
