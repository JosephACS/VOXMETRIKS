"""Backfill public dim_track rows for already-published submissions."""

from __future__ import annotations

import logging
from typing import Any

import duckdb

from app.packages.catalog_publishing.infrastructure.schema import (
    DEMO_WAREHOUSE_TRACK_ID_MIN,
)

logger = logging.getLogger("voxmetrik.catalog_publishing.sync")


def sync_published_tracks_to_catalog(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """
    Idempotent repair: every ``published`` submission track with a warehouse id
    gets a discoverable ``dim_track`` row (no duplicates).
    """
    from app.packages.catalog_publishing.application.use_cases import (
        CatalogPublishingUseCases,
        _table_exists,
    )

    if not _table_exists(conn, "app_release_submission") or not _table_exists(
        conn, "dim_track"
    ):
        return {"synced": 0, "skipped": True}

    # Repair known demo collision: withdrawn must not share published warehouse id.
    withdrawn_wh = DEMO_WAREHOUSE_TRACK_ID_MIN + 2
    try:
        conn.execute(
            """
            UPDATE app_release_submission_track st
            SET warehouse_track_id = ?
            FROM app_release_submission s
            WHERE st.submission_id = s.id
              AND s.idempotency_key = 'demo-s031-withdrawn'
              AND st.warehouse_track_id = ?
            """,
            [withdrawn_wh, DEMO_WAREHOUSE_TRACK_ID_MIN],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("withdrawn warehouse id repair skipped: %s", exc)

    uc = CatalogPublishingUseCases(conn)
    rows = conn.execute(
        """
        SELECT
            st.id, st.submission_id, st.title, st.duration_ms, st.warehouse_track_id,
            s.title AS release_title, s.artist_profile_id, s.is_demo, s.status,
            s.organization_id
        FROM app_release_submission_track st
        JOIN app_release_submission s ON s.id = st.submission_id
        WHERE s.status = 'published'
          AND st.warehouse_track_id IS NOT NULL
          AND st.warehouse_track_id >= ?
        """,
        [DEMO_WAREHOUSE_TRACK_ID_MIN],
    ).fetchall()

    synced = 0
    for r in rows:
        track = {
            "id": int(r[0]),
            "title": r[2] or r[5] or "Untitled",
            "duration_ms": r[3] or 0,
            "warehouse_track_id": int(r[4]),
        }
        sub = {
            "title": r[5],
            "artist_profile_id": r[6],
            "is_demo": bool(r[7]),
            "status": r[8],
            "organization_id": r[9],
        }
        wtid = int(r[4])
        uc._upsert_public_dim_track(wtid, track, sub)
        cover = conn.execute(
            "SELECT cover_media_id FROM app_release_submission WHERE id = ?",
            [int(r[1])],
        ).fetchone()
        if cover and cover[0]:
            uc._upsert_cover(wtid, int(cover[0]))
        audio = conn.execute(
            """
            SELECT audio_media_id FROM app_release_submission_track WHERE id = ?
            """,
            [int(r[0])],
        ).fetchone()
        if audio and audio[0]:
            playable = f"/api/v1/media/{int(audio[0])}/content"
            uc._upsert_audio_source(wtid, playable)
        synced += 1

    # Align legacy seed track titles for search ("Published Track" → release name)
    try:
        conn.execute(
            """
            UPDATE app_release_submission_track st
            SET title = 'Published Single'
            FROM app_release_submission s
            WHERE st.submission_id = s.id
              AND s.idempotency_key = 'demo-s031-published'
              AND (st.title IS NULL OR lower(st.title) IN ('published track', 'track'))
            """
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("published title align skipped: %s", exc)

    logger.info("Published catalog sync: %s track(s) ensured", synced)
    return {"synced": synced, "skipped": False}
