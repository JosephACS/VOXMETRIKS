# -*- coding: utf-8 -*-
"""Refresh stale YouTube audio-source metadata in small batches.

Usage (from apps/backend):
  python -m app.packages.streaming.services.audio.refresh_youtube_metadata
  python -m app.packages.streaming.services.audio.refresh_youtube_metadata --limit 25 --max-age-days 30

Does not run on Discover load. Safe to schedule via cron/Task Scheduler.
Never downloads audiovisual files — only re-validates via YouTube Data API.
"""

from __future__ import annotations

import argparse
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

import duckdb

from app.core.config import get_settings
from app.core.database import get_connection, table_exists
from app.core.time_util import utc_now
from app.packages.streaming.services.audio.cache import (
    STATUS_DISABLED,
    STATUS_NOT_FOUND,
    STATUS_OK,
    migrate_audio_source_columns,
    write_cache,
)
from app.packages.streaming.services.audio.models import ResolvedSource
from app.packages.streaming.services.audio.youtube_provider import YouTubeProvider

logger = logging.getLogger(__name__)


def _select_stale(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int,
    max_age_days: int,
) -> List[Dict[str, Any]]:
    migrate_audio_source_columns(conn)
    cutoff = utc_now() - timedelta(days=max_age_days)
    rows = conn.execute(
        """
        SELECT track_id, youtube_video_id, source_ref, status,
               COALESCE(last_checked_at, resolved_at) AS checked_at
        FROM app_track_audio_source
        WHERE provider = 'youtube'
          AND COALESCE(youtube_video_id, source_ref, '') <> ''
          AND (
            COALESCE(last_checked_at, resolved_at) IS NULL
            OR COALESCE(last_checked_at, resolved_at) < ?
          )
        ORDER BY COALESCE(last_checked_at, resolved_at) ASC NULLS FIRST
        LIMIT ?
        """,
        [cutoff, limit],
    ).fetchall()
    out = []
    for r in rows:
        vid = (r[1] or r[2] or "").strip()
        out.append(
            {
                "track_id": int(r[0]),
                "video_id": vid,
                "status": r[3],
                "checked_at": r[4],
            }
        )
    return out


def refresh_youtube_metadata_batch(
    conn: duckdb.DuckDBPyConnection,
    *,
    limit: int = 25,
    max_age_days: int = 30,
) -> Dict[str, Any]:
    """Re-validate a small batch of YouTube sources. Never blocks Discover."""
    if not table_exists(conn, "app_track_audio_source"):
        return {"ok": False, "reason": "no_table", "processed": 0}

    api_key = get_settings().youtube_api_key.strip()
    if not api_key:
        return {"ok": False, "reason": "youtube_not_configured", "processed": 0}

    stale = _select_stale(conn, limit=limit, max_age_days=max_age_days)
    if not stale:
        return {"ok": True, "processed": 0, "updated": 0, "removed": 0, "errors": 0}

    yt = YouTubeProvider()
    ids = [s["video_id"] for s in stale if s["video_id"]]
    details: Optional[Dict[str, Any]] = None
    try:
        details = yt._fetch_video_details(ids, api_key)
    except Exception as exc:
        logger.warning("YouTube metadata refresh batch failed: %s", type(exc).__name__)
        return {
            "ok": False,
            "reason": "provider_error",
            "processed": 0,
            "updated": 0,
            "removed": 0,
            "errors": len(stale),
        }

    # None = provider/quota/network failure — never treat as "all not_found".
    if details is None:
        return {
            "ok": False,
            "reason": "provider_error",
            "processed": 0,
            "updated": 0,
            "removed": 0,
            "errors": len(stale),
        }

    updated = removed = errors = 0
    now = utc_now()
    for item in stale:
        tid = item["track_id"]
        vid = item["video_id"]
        try:
            meta = details.get(vid)
            if not meta:
                write_cache(
                    conn,
                    ResolvedSource(
                        track_id=tid,
                        provider="youtube",
                        status=STATUS_NOT_FOUND,
                        youtube_video_id=vid,
                        source_ref=vid,
                        query="refresh:removed",
                        confidence_score=0.0,
                    ),
                )
                conn.execute(
                    "UPDATE app_track_audio_source SET last_checked_at = ? WHERE track_id = ?",
                    [now, tid],
                )
                removed += 1
                continue

            write_cache(
                conn,
                ResolvedSource(
                    track_id=tid,
                    provider="youtube",
                    status=STATUS_OK,
                    youtube_video_id=vid,
                    source_ref=vid,
                    query=f"{meta.get('title') or ''} {meta.get('channel_title') or ''}".strip(),
                    confidence_score=0.95,
                ),
                preserve_failure_count=True,
            )
            conn.execute(
                "UPDATE app_track_audio_source SET last_checked_at = ? WHERE track_id = ?",
                [now, tid],
            )
            updated += 1
        except Exception:
            errors += 1
            logger.exception("Failed refreshing track_id=%s", tid)

    return {
        "ok": True,
        "processed": len(stale),
        "updated": updated,
        "removed": removed,
        "errors": errors,
        "max_age_days": max_age_days,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh stale YouTube audio metadata")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--max-age-days", type=int, default=30)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    conn = get_connection()
    result = refresh_youtube_metadata_batch(
        conn, limit=args.limit, max_age_days=args.max_age_days
    )
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
