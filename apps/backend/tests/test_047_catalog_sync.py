# -*- coding: utf-8 -*-
"""Spec 047 — published catalog sync projects to dim_track (idempotent)."""

from __future__ import annotations

from unittest.mock import patch

import duckdb
import pytest

from app.core.schema_bootstrap import reset_schema_ready_for_tests
from app.core.time_util import utc_now
from app.packages.catalog_publishing.application.sync_catalog import (
    sync_published_tracks_to_catalog,
)
from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.infrastructure.schema import (
    DEMO_WAREHOUSE_TRACK_ID_MIN,
    ensure_catalog_publishing_tables,
)


def _seed_published(conn: duckdb.DuckDBPyConnection) -> int:
    reset_schema_ready_for_tests()
    ensure_catalog_publishing_tables(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY,
            nombre_track VARCHAR,
            id_artista INTEGER,
            duration_ms INTEGER,
            popularity INTEGER,
            search_fold VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_artista (
            id_artista INTEGER PRIMARY KEY,
            nombre_artista VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_track_audio_source (
            track_id INTEGER PRIMARY KEY,
            provider VARCHAR,
            youtube_video_id VARCHAR,
            source_ref VARCHAR,
            playable_url VARCHAR,
            query VARCHAR,
            status VARCHAR,
            failure_count INTEGER,
            confidence_score DOUBLE,
            resolved_at TIMESTAMP,
            last_checked_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_track_cover (
            track_id INTEGER PRIMARY KEY,
            image_url VARCHAR,
            status VARCHAR,
            resolved_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_artist_profile (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER,
            display_name VARCHAR,
            warehouse_artist_id INTEGER,
            updated_at TIMESTAMP
        )
        """
    )
    now = utc_now()
    conn.execute(
        "INSERT INTO app_artist_profile VALUES (1, 0, 'Sync Artist', NULL, ?)",
        [now],
    )
    wtid = DEMO_WAREHOUSE_TRACK_ID_MIN + 11
    conn.execute(
        """
        INSERT INTO app_release_submission (
            id, organization_id, artist_profile_id, release_type, title, status,
            created_by, is_demo, cover_media_id, idempotency_key, created_at, updated_at
        ) VALUES (1, 0, 1, 'single', 'Published Single', 'published', 1, TRUE, 77,
                  'demo-sync-047', ?, ?)
        """,
        [now, now],
    )
    conn.execute(
        """
        INSERT INTO app_release_submission_track (
            id, submission_id, title, duration_ms, warehouse_track_id, audio_media_id,
            track_number, disc_number, created_at, updated_at
        ) VALUES (1, 1, 'Published Track', 180000, ?, 88, 1, 1, ?, ?)
        """,
        [wtid, now, now],
    )
    return wtid


def test_sync_projects_track_audio_cover_idempotent():
    conn = duckdb.connect(":memory:")
    wtid = _seed_published(conn)

    first = sync_published_tracks_to_catalog(conn)
    assert first["skipped"] is False
    assert first["synced"] == 1
    assert (
        int(conn.execute("SELECT COUNT(*) FROM dim_track WHERE id_track = ?", [wtid]).fetchone()[0])
        == 1
    )
    title = conn.execute(
        "SELECT nombre_track FROM dim_track WHERE id_track = ?", [wtid]
    ).fetchone()[0]
    assert title
    assert (
        int(
            conn.execute(
                "SELECT COUNT(*) FROM app_track_audio_source WHERE track_id = ?", [wtid]
            ).fetchone()[0]
        )
        == 1
    )
    audio = conn.execute(
        "SELECT playable_url, provider FROM app_track_audio_source WHERE track_id = ?",
        [wtid],
    ).fetchone()
    assert audio[1] == "local_published"
    assert "/api/v1/media/88/content" in str(audio[0])
    cover = conn.execute(
        "SELECT image_url FROM app_track_cover WHERE track_id = ?", [wtid]
    ).fetchone()
    assert cover and "/api/v1/media/77/content" in str(cover[0])

    with patch.object(
        CatalogPublishingUseCases, "_apply_dim_track_replace"
    ) as apply_dim:
        second = sync_published_tracks_to_catalog(conn)
    assert second["synced"] == 1
    apply_dim.assert_not_called()
    assert (
        int(conn.execute("SELECT COUNT(*) FROM dim_track WHERE id_track = ?", [wtid]).fetchone()[0])
        == 1
    )
    assert int(conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]) == 1
    conn.close()


def test_sync_real_change_updates_dim_track():
    conn = duckdb.connect(":memory:")
    wtid = _seed_published(conn)
    sync_published_tracks_to_catalog(conn)
    before = conn.execute(
        "SELECT nombre_track FROM dim_track WHERE id_track = ?", [wtid]
    ).fetchone()[0]
    conn.execute(
        "UPDATE app_release_submission SET title = 'Brand New Release' WHERE id = 1"
    )
    conn.execute(
        "UPDATE app_release_submission_track SET title = 'Brand New Track' WHERE id = 1"
    )
    sync_published_tracks_to_catalog(conn)
    after = conn.execute(
        "SELECT nombre_track FROM dim_track WHERE id_track = ?", [wtid]
    ).fetchone()[0]
    assert after != before
    assert "Brand New" in str(after)
    assert (
        int(conn.execute("SELECT COUNT(*) FROM dim_track WHERE id_track = ?", [wtid]).fetchone()[0])
        == 1
    )
    conn.close()


def test_upsert_update_rollback_on_midflight_failure():
    """Mid-flight failure inside transactional UPDATE rolls back prior row."""
    conn = duckdb.connect(":memory:")
    wtid = _seed_published(conn)
    sync_published_tracks_to_catalog(conn)
    original = conn.execute(
        "SELECT nombre_track, duration_ms, popularity FROM dim_track WHERE id_track = ?",
        [wtid],
    ).fetchone()
    assert original

    uc = CatalogPublishingUseCases(conn)
    track = {
        "id": 1,
        "title": "Changed Title Forever",
        "duration_ms": 999000,
        "warehouse_track_id": wtid,
    }
    sub = {
        "title": "Changed Release",
        "artist_profile_id": 1,
        "is_demo": True,
        "status": "published",
        "organization_id": 0,
    }
    planned = uc._dim_track_canonical_values(wtid, track, sub)
    assert planned is not None
    fields, values = planned
    assert not uc._dim_track_row_matches(wtid, fields, values)

    def flaky_apply(_wtid, _fields, _values):
        uc._conn.execute(
            "UPDATE dim_track SET nombre_track = ? WHERE id_track = ?",
            ["partial-corrupt", wtid],
        )
        raise RuntimeError("injected update failure")

    with patch.object(uc, "_apply_dim_track_replace", side_effect=flaky_apply):
        with pytest.raises(RuntimeError, match="injected update failure"):
            uc._upsert_public_dim_track(wtid, track, sub)

    restored = conn.execute(
        "SELECT nombre_track, duration_ms, popularity FROM dim_track WHERE id_track = ?",
        [wtid],
    ).fetchone()
    assert restored == original
    assert (
        int(conn.execute("SELECT COUNT(*) FROM dim_track WHERE id_track = ?", [wtid]).fetchone()[0])
        == 1
    )
    conn.close()


def test_upsert_audio_source_normalizes_contaminated_local_row():
    """Contaminated local_published row is normalized; second upsert is a no-op."""
    conn = duckdb.connect(":memory:")
    wtid = _seed_published(conn)
    sync_published_tracks_to_catalog(conn)
    playable = "/api/v1/media/88/content"
    now = utc_now()
    conn.execute(
        """
        UPDATE app_track_audio_source
        SET youtube_video_id = 'contaminatedVid',
            failure_count = 3,
            confidence_score = 0.25,
            resolved_at = ?,
            last_checked_at = ?
        WHERE track_id = ?
        """,
        [now, now, wtid],
    )
    dirty = conn.execute(
        """
        SELECT youtube_video_id, failure_count, confidence_score
        FROM app_track_audio_source WHERE track_id = ?
        """,
        [wtid],
    ).fetchone()
    assert dirty[0] == "contaminatedVid"
    assert int(dirty[1]) == 3
    assert float(dirty[2]) == 0.25

    uc = CatalogPublishingUseCases(conn)
    assert uc._audio_source_matches(wtid, playable) is False
    wrote = uc._upsert_audio_source(wtid, playable)
    assert wrote is True
    clean = conn.execute(
        """
        SELECT provider, youtube_video_id, source_ref, playable_url,
               query, status, failure_count, confidence_score
        FROM app_track_audio_source WHERE track_id = ?
        """,
        [wtid],
    ).fetchone()
    assert clean[0] == "local_published"
    assert clean[1] is None
    assert str(clean[2]) == str(wtid)
    assert clean[3] == playable
    assert clean[4] == "local_published"
    assert clean[5] == "ok"
    assert int(clean[6]) == 0
    assert float(clean[7]) == 1.0
    assert uc._audio_source_matches(wtid, playable) is True

    with patch.object(uc, "_apply_audio_source_replace") as apply_audio:
        second = uc._upsert_audio_source(wtid, playable)
    assert second is False
    apply_audio.assert_not_called()
    conn.close()


def test_demo_warehouse_id_9000000_remains_unique():
    conn = duckdb.connect(":memory:")
    wtid = DEMO_WAREHOUSE_TRACK_ID_MIN
    _seed_published(conn)
    # Force the seeded track onto the canonical demo id.
    conn.execute(
        "UPDATE app_release_submission_track SET warehouse_track_id = ?", [wtid]
    )
    sync_published_tracks_to_catalog(conn)
    sync_published_tracks_to_catalog(conn)
    n = int(
        conn.execute(
            "SELECT COUNT(*) FROM dim_track WHERE id_track = ?", [wtid]
        ).fetchone()[0]
    )
    assert n == 1
    assert int(conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]) == 1
    conn.close()


def test_sync_skipped_without_dim_track():
    conn = duckdb.connect(":memory:")
    ensure_catalog_publishing_tables(conn)
    out = sync_published_tracks_to_catalog(conn)
    assert out["skipped"] is True
    assert out["synced"] == 0
    conn.close()


def test_sync_real_failure_is_not_disguised():
    conn = duckdb.connect(":memory:")
    _seed_published(conn)
    with patch.object(
        CatalogPublishingUseCases,
        "_dim_track_canonical_values",
        side_effect=RuntimeError("sync boom"),
    ):
        with pytest.raises(RuntimeError, match="sync boom"):
            sync_published_tracks_to_catalog(conn)
    assert int(conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]) == 0
    conn.close()


def test_upsert_public_dim_track_method_exists():
    assert hasattr(CatalogPublishingUseCases, "_upsert_public_dim_track")
    assert callable(CatalogPublishingUseCases._upsert_public_dim_track)
