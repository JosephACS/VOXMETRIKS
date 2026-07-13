"""DuckDB cache for resolved audio sources."""

from __future__ import annotations

from typing import Any, Dict, Optional

import duckdb

from app.core.config import get_settings
from app.core.time_util import utc_now

from .models import ResolvedSource

STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_DISABLED = "disabled"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"

_MAX_FAILURES_BEFORE_STALE = 3


def migrate_audio_source_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Add optional columns without breaking existing rows."""
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'app_track_audio_source'"
        ).fetchall()
    }
    additions = {
        "source_ref": "VARCHAR",
        "playable_url": "VARCHAR",
        "failure_count": "INTEGER DEFAULT 0",
        "last_checked_at": "TIMESTAMP",
        "confidence_score": "DOUBLE",
    }
    for col, col_type in additions.items():
        if col not in existing:
            conn.execute(
                f"ALTER TABLE app_track_audio_source ADD COLUMN {col} {col_type}"
            )


def read_cache(
    conn: duckdb.DuckDBPyConnection, track_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT track_id, provider, youtube_video_id, source_ref, playable_url,
               query, status, failure_count, confidence_score, resolved_at
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
        "source_ref": row[3],
        "playable_url": row[4],
        "query": row[5],
        "status": row[6],
        "failure_count": int(row[7] or 0),
        "confidence_score": row[8],
        "resolved_at": row[9],
    }


def is_cache_usable(cached: Dict[str, Any]) -> bool:
    status = cached["status"]
    if status not in (STATUS_OK, STATUS_NOT_FOUND, STATUS_DISABLED):
        return False
    if status == STATUS_OK and int(cached.get("failure_count") or 0) >= _MAX_FAILURES_BEFORE_STALE:
        return False
    # Soft TTL: retry external lookup after negative cache ages out.
    if status in (STATUS_NOT_FOUND, STATUS_DISABLED):
        resolved_at = cached.get("resolved_at")
        if resolved_at is not None:
            try:
                ttl = float(get_settings().audio_not_found_ttl_sec)
                age_s = (utc_now() - resolved_at).total_seconds()
                if age_s > ttl:
                    return False
            except Exception:
                return False
    return True


def write_cache(conn: duckdb.DuckDBPyConnection, resolved: ResolvedSource) -> None:
    yt_id = resolved.youtube_video_id
    if resolved.provider == "youtube" and resolved.source_ref and not yt_id:
        yt_id = resolved.source_ref
    conn.execute("DELETE FROM app_track_audio_source WHERE track_id = ?", [resolved.track_id])
    conn.execute(
        """
        INSERT INTO app_track_audio_source
            (track_id, provider, youtube_video_id, source_ref, playable_url,
             query, status, failure_count, confidence_score, resolved_at, last_checked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """,
        [
            resolved.track_id,
            resolved.provider,
            yt_id,
            resolved.source_ref,
            resolved.playable_url,
            resolved.query,
            resolved.status,
            resolved.confidence_score,
            utc_now(),
            utc_now(),
        ],
    )


def mark_failure(conn: duckdb.DuckDBPyConnection, track_id: int) -> None:
    conn.execute(
        """
        UPDATE app_track_audio_source
        SET failure_count = COALESCE(failure_count, 0) + 1,
            last_checked_at = ?
        WHERE track_id = ?
        """,
        [utc_now(), track_id],
    )
