"""Audius public API provider (no API key required)."""

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
    build_search_query_variants,
    normalize_track_meta,
    title_similarity,
)
from .models import ResolvedSource, TrackContext

logger = logging.getLogger(__name__)

_AUDIUS_HOST = "https://api.audius.co"
_APP_NAME = "VOXMETRIKS"
_REQUEST_TIMEOUT = float(get_settings().audio_provider_timeout_sec or 12.0)
_SEARCH_LIMIT = 8
_MAX_QUERY_ATTEMPTS = 4

_BAD_TITLE_RE = re.compile(
    r"\b(cover|remix|live|karaoke|instrumental|nightcore|slowed|clip)\b",
    re.IGNORECASE,
)


class AudiusProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "audius"

    def resolve(self, track: TrackContext) -> ResolvedSource:
        meta = normalize_track_meta(track.track_name, track.artist_name)
        queries = build_search_query_variants(
            track.track_name, track.artist_name, max_variants=_MAX_QUERY_ATTEMPTS
        )
        # Audius does not need "official audio" suffix as much — prefer plain variants too.
        # Prefer cleaned titles (without "feat./with …") so warehouse titles like
        # "Be Kind (with Halsey)" still match Audius catalog entries.
        plain: List[str] = []
        for title in meta.title_variants:
            if meta.primary_artist:
                plain.append(f"{title} {meta.primary_artist}".strip())
            if meta.all_artists_joined and meta.all_artists_joined != meta.primary_artist:
                plain.append(f"{title} {meta.all_artists_joined}".strip())
            plain.append(title)
        for q in plain:
            if q and q not in queries:
                queries.append(q)
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

    def _resolve_query(
        self, track: TrackContext, meta, query: str
    ) -> ResolvedSource:
        try:
            resp = httpx.get(
                f"{_AUDIUS_HOST}/v1/tracks/search",
                params={"query": query, "app_name": _APP_NAME, "limit": _SEARCH_LIMIT},
                timeout=_REQUEST_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            logger.warning("Audius search failed for %r: %s", query, exc)
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=query,
            )

        if resp.status_code != 200:
            logger.warning("Audius search returned %s", resp.status_code)
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_ERROR,
                query=query,
            )

        items: List[Dict[str, Any]] = resp.json().get("data") or []
        best = self._pick_best(items, track, meta)
        if not best:
            return ResolvedSource(
                track_id=track.track_id,
                provider=self.name,
                status=STATUS_NOT_FOUND,
                query=query,
            )

        audius_id = str(best["id"])
        stream_url = f"{_AUDIUS_HOST}/v1/tracks/{audius_id}/stream?app_name={_APP_NAME}"
        return ResolvedSource(
            track_id=track.track_id,
            provider=self.name,
            status=STATUS_OK,
            source_ref=audius_id,
            playable_url=stream_url,
            query=query,
            confidence_score=best.get("_score"),
        )

    def _pick_best(
        self, items: List[Dict[str, Any]], track: TrackContext, meta
    ) -> Optional[Dict[str, Any]]:
        artists = list(meta.artists)
        expect_titles = [
            t
            for t in (
                meta.original_title,
                meta.clean_title,
                *meta.title_variants,
                track.track_name,
            )
            if t
        ]
        # Deduplicate while preserving order.
        seen_titles: set[str] = set()
        uniq_expect: List[str] = []
        for t in expect_titles:
            key = t.casefold()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            uniq_expect.append(t)

        best: Optional[Dict[str, Any]] = None
        best_score = -1.0

        for item in items:
            title = (item.get("title") or "").strip()
            user = item.get("user") or {}
            artist = (user.get("name") or "").strip()
            if not title:
                continue
            if _BAD_TITLE_RE.search(title):
                continue

            sim = max((title_similarity(title, expected) for expected in uniq_expect), default=0.0)
            if sim < 0.22:
                continue

            a_score = artist_match_score(f"{title} {artist}", artists)
            if artists and a_score < 0.30:
                continue

            score = sim * 50.0 + a_score * 35.0

            duration = int(item.get("duration") or 0)
            # Skip hard duration rejects when the catalog title is a speed/edit variant —
            # Audius usually has the normal-tempo track.
            speed_variant = bool(
                re.search(r"\b(sped\s*up|slowed|nightcore|speed\s*up)\b", expect_titles[0] or "", re.I)
            )
            if track.duration_ms and duration > 0 and not speed_variant:
                track_sec = track.duration_ms / 1000.0
                ratio = abs(duration - track_sec) / track_sec
                if ratio > 0.35:
                    continue
                if ratio <= 0.12:
                    score += 40.0
                elif ratio <= 0.25:
                    score += 20.0
                elif ratio > 0.5:
                    score -= 25.0

            if score > best_score:
                best_score = score
                best = {**item, "_score": round(min(0.99, score / 125.0), 3)}

        if best_score < 30.0:
            return None
        return best
