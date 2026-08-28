# -*- coding: utf-8 -*-
"""Central playback availability predicates for consumer music surfaces."""

from __future__ import annotations

from app.core.database import table_exists

# Consumer-facing playback_status values
PLAYABLE = "playable"
UNCHECKED = "unchecked"
UNAVAILABLE = "unavailable"
FAILED = "failed"
MISSING = "missing"
REMOVED = "removed"

_MAX_FAILURES = 3


def playable_track_sql(conn, *, track_alias: str = "dt") -> str:
    """
    SQL boolean predicate: track has a currently usable external/local source.

    Requires ``app_track_audio_source``. If the table is missing, returns false
    (consumer surfaces stay empty rather than listing non-playable rows).
    """
    if not table_exists(conn, "app_track_audio_source"):
        return "1=0"
    return f"""
    EXISTS (
      SELECT 1
      FROM app_track_audio_source src
      WHERE src.track_id = {track_alias}.id_track
        AND src.status = 'ok'
        AND COALESCE(src.failure_count, 0) < {_MAX_FAILURES}
        AND src.provider IN ('deezer', 'local_published')
        AND COALESCE(src.playable_url, src.source_ref, '') <> ''
    )
    """


def playback_status_for_cache(cached: dict | None) -> str:
    """Map a cache row (or absence) to a consumer playback_status."""
    if not cached:
        return MISSING
    status = (cached.get("status") or "").lower()
    provider = (cached.get("provider") or "").lower()
    failures = int(cached.get("failure_count") or 0)
    if status == "ok" and provider in {"deezer", "local_published"} and failures < _MAX_FAILURES:
        return PLAYABLE
    if status == "disabled":
        return REMOVED
    if status == "error" or failures >= _MAX_FAILURES:
        return FAILED
    if status in {"not_found"}:
        return UNAVAILABLE
    if status == "pending":
        return UNCHECKED
    return UNAVAILABLE
