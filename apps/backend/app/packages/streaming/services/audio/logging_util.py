"""Internal resolution observability (not exposed to API clients)."""

from __future__ import annotations

import logging

from .models import ResolutionLog

logger = logging.getLogger("voxmetriks.audio.resolver")


def log_resolution(entry: ResolutionLog) -> None:
    msg = (
        "audio_resolve track=%s provider=%s outcome=%s elapsed_ms=%.1f "
        "cache=%s fallback=%s"
    )
    args = (
        entry.track_id,
        entry.provider,
        entry.outcome,
        entry.elapsed_ms,
        entry.from_cache,
        entry.fallback,
    )
    if entry.error:
        logger.warning(msg + " error=%s", *args, entry.error)
    else:
        logger.info(msg, *args)
