"""Deezer public-search provider used for short fallback previews.

The Deezer API exposes a track-specific ``preview`` URL without an app token.
Those URLs are deliberately treated as previews (not full catalog streams):
the browser plays them through the normal HTMLAudioElement for up to 30 seconds.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

from .base import AudioProvider
from .cache import STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK
from .metadata_normalize import (
    artist_match_score,
    normalize_track_meta,
    token_set,
    title_similarity,
)
from .models import ResolvedSource, TrackContext

logger = logging.getLogger(__name__)

_DEEZER_SEARCH_URL = "https://api.deezer.com/search"
_REQUEST_TIMEOUT = float(get_settings().audio_provider_timeout_sec or 12.0)
_SEARCH_LIMIT = 10
_MAX_QUERY_ATTEMPTS = 4

_BAD_TITLE_RE = re.compile(
    r"\b(cover|karaoke|instrumental|nightcore|slowed|sped\s*up|live\s+version)\b",
    re.IGNORECASE,
)


class DeezerProvider(AudioProvider):
    """Resolve a song to Deezer's public 30-second preview URL."""

    @property
    def name(self) -> str:
        return "deezer"

    def resolve(self, track: TrackContext) -> ResolvedSource:
        meta = normalize_track_meta(track.track_name, track.artist_name)
        # Deezer's advanced search syntax is more precise when the title and
        # artist are quoted. Keep the query list short so one search cannot
        # spend the whole playback timeout on variants that add YouTube-only
        # terms such as "official audio".
        queries: List[str] = []

        def add(query: str) -> None:
            query = " ".join(query.split())
            if query and query not in queries:
                queries.append(query)

        for title in meta.title_variants:
            if meta.primary_artist:
                add(f'track:"{title}" artist:"{meta.primary_artist}"')
            if meta.all_artists_joined and meta.all_artists_joined != meta.primary_artist:
                add(f'track:"{title}" artist:"{meta.all_artists_joined}"')
            add(f'track:"{title}"')
        queries = queries[: max(_MAX_QUERY_ATTEMPTS, 6)] or [track.track_name]

        last_query = queries[0]
        for query in queries:
            last_query = query
            result = self._resolve_query(track, meta, query)
            if result.status == STATUS_OK:
                return result
            if result.status == STATUS_ERROR:
                continue

        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=STATUS_NOT_FOUND,
            query=last_query,
        )

    def _resolve_query(self, track: TrackContext, meta, query: str) -> ResolvedSource:
        try:
            response = httpx.get(
                _DEEZER_SEARCH_URL,
                params={"q": query, "limit": _SEARCH_LIMIT},
                timeout=_REQUEST_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            logger.warning("Deezer search failed for %r: %s", query, exc)
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=query,
            )

        if response.status_code != 200:
            logger.warning("Deezer search returned %s", response.status_code)
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=query,
            )

        try:
            items: List[Dict[str, Any]] = response.json().get("data") or []
        except (TypeError, ValueError):
            items = []

        best = self._pick_best(items, track, meta)
        if not best:
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_NOT_FOUND,
                query=query,
            )

        preview_url = str(best.get("preview") or "").strip()
        if not preview_url:
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_NOT_FOUND,
                query=query,
            )

        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=STATUS_OK,
            source_ref=str(best.get("id") or ""),
            playable_url=preview_url,
            query=query,
            confidence_score=best.get("_score"),
        )

    def _pick_best(
        self, items: List[Dict[str, Any]], track: TrackContext, meta
    ) -> Optional[Dict[str, Any]]:
        expected_titles = [
            value
            for value in (
                meta.original_title,
                meta.clean_title,
                *meta.title_variants,
                track.track_name,
            )
            if value
        ]
        best: Optional[Dict[str, Any]] = None
        best_score = -1.0

        for item in items:
            title = str(item.get("title") or "").strip()
            artist_obj = item.get("artist") or {}
            artist = str(artist_obj.get("name") or "").strip()
            preview = str(item.get("preview") or "").strip()
            if not title or not preview or _BAD_TITLE_RE.search(title):
                continue

            similarity = max(
                (title_similarity(title, expected) for expected in expected_titles),
                default=0.0,
            )
            if similarity < 0.45:
                continue

            artist_score = artist_match_score(f"{title} {artist}", meta.artists)
            if meta.artists and artist_score < 0.30:
                continue
            # ``artist_match_score`` intentionally allows soft matches for
            # YouTube channel names. Deezer has a structured artist field, so
            # require most primary-artist tokens to be present to avoid a
            # tempting but unrelated result such as "Another Artist".
            primary_tokens = token_set(meta.primary_artist)
            candidate_tokens = token_set(artist)
            if primary_tokens:
                overlap = len(primary_tokens & candidate_tokens) / len(primary_tokens)
                if overlap < 0.6:
                    continue

            score = similarity * 60.0 + artist_score * 35.0
            duration = int(item.get("duration") or 0)
            if track.duration_ms and duration > 0:
                track_seconds = track.duration_ms / 1000.0
                ratio = abs(duration - track_seconds) / track_seconds
                if ratio > 0.35:
                    continue
                if ratio <= 0.12:
                    score += 20.0
                elif ratio <= 0.25:
                    score += 8.0

            if score > best_score:
                best_score = score
                best = {**item, "_score": round(min(0.99, score / 115.0), 3)}

        if best_score < 35.0:
            return None
        return best
