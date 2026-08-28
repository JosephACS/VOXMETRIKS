"""Central Deezer preview resolver for the consumer catalog.

Spotify full-track playback is intentionally handled in the browser through
the Web Playback SDK. The backend only resolves the no-auth Deezer preview
fallback (and local published audio).
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Sequence

import duckdb

from .base import AudioProvider
from .cache import (
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_OK,
    is_cache_usable,
    read_cache,
    write_cache,
)
from .deezer_provider import DeezerProvider
from .logging_util import log_resolution
from .models import ResolutionLog, ResolvedSource, TrackContext

logger = logging.getLogger(__name__)

_DEFAULT_CHAIN: List[AudioProvider] = [
    DeezerProvider(),
]


def _parse_exclude_refs(exclude_source_ref: Optional[str]) -> Optional[set[str]]:
    if not exclude_source_ref:
        return None
    refs = {part.strip() for part in str(exclude_source_ref).split(",") if part.strip()}
    return refs or None


def build_track_context(
    conn: duckdb.DuckDBPyConnection,
    track_id: int,
    *,
    exclude_source_refs: Optional[set[str]] = None,
) -> Optional[TrackContext]:
    row = conn.execute(
        """
        SELECT dt.nombre_track, da.nombre_artista, dt.duration_ms
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.id_track = ?
        """,
        [track_id],
    ).fetchone()
    if not row or not (row[0] or "").strip():
        return None
    return TrackContext(
        track_id=track_id,
        track_name=(row[0] or "").strip(),
        artist_name=(row[1] or "").strip(),
        duration_ms=int(row[2]) if row[2] is not None else None,
        exclude_source_refs=frozenset(exclude_source_refs or ()),
    )


class AudioResolver:
    """Resolve playable audio through Deezer preview, with cache."""

    def __init__(self, providers: Optional[Sequence[AudioProvider]] = None) -> None:
        self._providers = list(providers or _DEFAULT_CHAIN)

    @property
    def providers(self) -> List[AudioProvider]:
        return list(self._providers)

    def resolve(
        self,
        conn: duckdb.DuckDBPyConnection,
        track_id: int,
        *,
        force: bool = False,
        skip_provider: Optional[str] = None,
        exclude_source_ref: Optional[str] = None,
    ) -> Optional[ResolvedSource]:
        excludes = _parse_exclude_refs(exclude_source_ref)
        ctx = build_track_context(conn, track_id, exclude_source_refs=excludes)
        if ctx is None:
            return None

        if not force:
            cached = read_cache(conn, track_id)
            if cached and cached.get("provider") == "local_published":
                log_resolution(
                    ResolutionLog(
                        track_id=track_id,
                        provider=cached["provider"],
                        outcome=cached["status"],
                        elapsed_ms=0.0,
                        from_cache=True,
                    )
                )
                return self._from_cache(cached)
            if (
                cached
                and self._can_reuse_cached_provider(cached.get("provider"))
                and is_cache_usable(cached)
            ):
                # Cached source is among excluded refs — must re-resolve.
                cached_ref = cached.get("source_ref")
                if excludes and cached_ref in excludes:
                    pass
                else:
                    log_resolution(
                        ResolutionLog(
                            track_id=track_id,
                            provider=cached["provider"],
                            outcome=cached["status"],
                            elapsed_ms=0.0,
                            from_cache=True,
                        )
                    )
                    return self._from_cache(cached)
        else:
            cached = read_cache(conn, track_id)
            if cached and cached.get("provider") == "local_published":
                return self._from_cache(cached)

        result = self._resolve_providers(ctx, skip_provider=skip_provider)
        if result is not None:
            # Never overwrite local_published with external providers
            existing = read_cache(conn, track_id)
            if existing and existing.get("provider") == "local_published":
                return self._from_cache(existing)
            # Never poison a playable cache with an ambiguous provider failure.
            if (
                result.status != STATUS_OK
                and existing
                and existing.get("status") == STATUS_OK
            ):
                return result
            if skip_provider and result.status != STATUS_OK:
                return result
            write_cache(conn, result)
        return result

    def resolve_background(
        self,
        track_id: int,
        *,
        force: bool = False,
        skip_provider: Optional[str] = None,
        exclude_source_ref: Optional[str] = None,
    ) -> Optional[ResolvedSource]:
        """Resolve without holding the DB lock across provider network I/O."""
        from app.core.database import get_connection

        from .cache import migrate_audio_source_columns

        conn = get_connection()
        migrate_audio_source_columns(conn)
        excludes = _parse_exclude_refs(exclude_source_ref)
        ctx = build_track_context(conn, track_id, exclude_source_refs=excludes)
        if ctx is None:
            return None
        if not force:
            cached = read_cache(conn, track_id)
            if cached and cached.get("provider") == "local_published":
                return self._from_cache(cached)
            if (
                cached
                and self._can_reuse_cached_provider(cached.get("provider"))
                and is_cache_usable(cached)
            ):
                cached_ref = cached.get("source_ref")
                if not (excludes and cached_ref in excludes):
                    return self._from_cache(cached)

        result = self._resolve_providers(ctx, skip_provider=skip_provider)
        if result is None:
            return None

        existing = read_cache(get_connection(), track_id)
        if existing and existing.get("provider") == "local_published":
            return self._from_cache(existing)
        if (
            result.status != STATUS_OK
            and existing
            and existing.get("status") == STATUS_OK
        ):
            return result
        if skip_provider and result.status != STATUS_OK:
            return result
        write_cache(get_connection(), result)
        return result

    def _resolve_providers(
        self,
        ctx: TrackContext,
        *,
        skip_provider: Optional[str] = None,
    ) -> Optional[ResolvedSource]:
        start = time.perf_counter()
        skip = {skip_provider} if skip_provider else set()
        last_not_found: Optional[ResolvedSource] = None
        track_id = ctx.track_id
        providers_tried: list[str] = []

        for provider in self._providers:
            if provider.name in skip:
                continue
            providers_tried.append(provider.name)
            try:
                result = provider.resolve(ctx)
            except Exception as exc:
                logger.exception("Provider %s raised for track %s", provider.name, track_id)
                log_resolution(
                    ResolutionLog(
                        track_id=track_id,
                        provider=provider.name,
                        outcome=STATUS_ERROR,
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        fallback=True,
                        error=str(exc),
                    )
                )
                continue

            elapsed = (time.perf_counter() - start) * 1000
            log_resolution(
                ResolutionLog(
                    track_id=track_id,
                    provider=provider.name,
                    outcome=result.status,
                    elapsed_ms=elapsed,
                    fallback=provider.name != self._providers[0].name,
                )
            )

            if result.status == STATUS_OK:
                return result

            if result.status == STATUS_ERROR:
                continue

            last_not_found = result

        if last_not_found:
            logger.info(
                "audio_source_unavailable track_id=%s title=%r artist=%r providers=%s",
                ctx.track_id,
                ctx.track_name,
                ctx.artist_name,
                ",".join(providers_tried),
            )
            return last_not_found

        logger.info(
            "audio_source_unavailable track_id=%s title=%r artist=%r providers=%s",
            ctx.track_id,
            ctx.track_name,
            ctx.artist_name,
            ",".join(providers_tried),
        )
        return ResolvedSource(
            track_id=track_id,
            provider=self._providers[-1].name if self._providers else "none",
            status=STATUS_NOT_FOUND,
            query=ctx.track_name,
        )

    @staticmethod
    def _from_cache(cached: dict) -> ResolvedSource:
        return ResolvedSource(
            track_id=int(cached["track_id"]),
            provider=cached["provider"],
            status=cached["status"],
            source_ref=cached.get("source_ref"),
            youtube_video_id=cached.get("youtube_video_id"),
            playable_url=cached.get("playable_url"),
            query=cached.get("query"),
            confidence_score=cached.get("confidence_score"),
        )

    def _can_reuse_cached_provider(self, provider: Optional[str]) -> bool:
        """Only reuse sources that belong to the active provider chain.

        Older builds could have cached external sources. They remain valid for
        an explicit/custom resolver, but the default chain only reuses Deezer
        previews or providers explicitly supplied by the caller.
        """
        if provider == "deezer":
            return True
        return bool(provider and any(item.name == provider for item in self._providers))


_default_resolver = AudioResolver()


def get_audio_resolver() -> AudioResolver:
    return _default_resolver
