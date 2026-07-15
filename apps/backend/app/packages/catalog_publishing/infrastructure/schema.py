"""Catalog publishing schema — Spec 031.

Idempotent CREATE TABLE IF NOT EXISTS for all publishing / media tables.
Additive only. Never mutates imported warehouse ids < 100000.

Warehouse track policy (publish):
  Prefer linking an existing warehouse_track_id on the submission track.
  If a new dim_track row is required for playback, insert ONLY with
  id >= 9_000_000 and title prefix ``[DEMO-SUBMIT]`` so demo publishes
  stay clearly separated from the imported ~89 740 catalog.
"""

from __future__ import annotations

import logging

import duckdb

logger = logging.getLogger("voxmetrik.catalog_publishing.schema")

# Reserved warehouse id space for published demo submissions only.
DEMO_WAREHOUSE_TRACK_ID_MIN = 9_000_000
DEMO_TRACK_TITLE_PREFIX = "[DEMO-SUBMIT]"

CATALOG_PUBLISHING_TABLES = (
    "app_release_submission",
    "app_release_submission_track",
    "app_release_contributor",
    "app_release_review",
    "app_release_review_issue",
    "app_release_status_history",
    "app_release_publication",
    "app_release_takedown",
    "app_media_asset",
    "app_media_upload",
    "app_media_validation",
    "app_catalog_duplicate_candidate",
    "app_catalog_publication_event",
    "app_artist_portal_access",
)


def ensure_catalog_publishing_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all catalog-publishing tables (idempotent, additive)."""
    _create_release_submission(conn)
    _create_release_submission_track(conn)
    _create_release_contributor(conn)
    _create_release_review(conn)
    _create_release_review_issue(conn)
    _create_release_status_history(conn)
    _create_release_publication(conn)
    _create_release_takedown(conn)
    _create_media_asset(conn)
    _create_media_upload(conn)
    _create_media_validation(conn)
    _create_duplicate_candidate(conn)
    _create_publication_event(conn)
    _create_artist_portal_access(conn)
    logger.info(
        "Catalog publishing schema ensured (%s tables)",
        len(CATALOG_PUBLISHING_TABLES),
    )


def _create_release_submission(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_submission (
            id                      INTEGER PRIMARY KEY,
            organization_id         INTEGER NOT NULL,
            artist_profile_id       INTEGER NOT NULL,
            release_type            VARCHAR NOT NULL DEFAULT 'single',
            title                   VARCHAR NOT NULL,
            version                 VARCHAR,
            label_name              VARCHAR,
            genre                   VARCHAR,
            language                VARCHAR,
            explicit                BOOLEAN NOT NULL DEFAULT FALSE,
            planned_release_date    DATE,
            actual_release_date     DATE,
            upc                     VARCHAR,
            cover_media_id          INTEGER,
            status                  VARCHAR NOT NULL DEFAULT 'draft',
            created_by              INTEGER NOT NULL,
            reviewer_id             INTEGER,
            rights_contract_id      INTEGER,
            catalog_asset_id        INTEGER,
            catalog_release_id      INTEGER,
            reject_reason           VARCHAR,
            withdraw_reason         VARCHAR,
            is_demo                 BOOLEAN NOT NULL DEFAULT FALSE,
            scheduled_at            TIMESTAMP,
            published_at            TIMESTAMP,
            idempotency_key         VARCHAR UNIQUE,
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (release_type IN ('single', 'ep', 'album', 'compilation')),
            CHECK (status IN (
                'draft', 'submitted', 'changes_requested', 'under_review',
                'approved', 'scheduled', 'published', 'suspended',
                'withdrawn', 'rejected', 'archived'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_submission_org
        ON app_release_submission(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_submission_artist
        ON app_release_submission(artist_profile_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_submission_status
        ON app_release_submission(status)
    """)


def _create_release_submission_track(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_submission_track (
            id                  INTEGER PRIMARY KEY,
            submission_id       INTEGER NOT NULL,
            title               VARCHAR NOT NULL,
            version             VARCHAR,
            track_number        INTEGER NOT NULL DEFAULT 1,
            disc_number         INTEGER NOT NULL DEFAULT 1,
            primary_artist_id   INTEGER,
            duration_ms         INTEGER,
            isrc                VARCHAR,
            explicit            BOOLEAN NOT NULL DEFAULT FALSE,
            audio_media_id      INTEGER,
            catalog_asset_id    INTEGER,
            rights_contract_id  INTEGER,
            warehouse_track_id  INTEGER,
            validation_status   VARCHAR NOT NULL DEFAULT 'pending',
            sort_order          INTEGER NOT NULL DEFAULT 0,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (validation_status IN ('ok', 'missing_audio', 'invalid', 'pending'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_sub_track_submission
        ON app_release_submission_track(submission_id)
    """)


def _create_release_contributor(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_contributor (
            id                  INTEGER PRIMARY KEY,
            submission_id       INTEGER NOT NULL,
            track_id            INTEGER,
            party_role          VARCHAR NOT NULL,
            artist_profile_id   INTEGER,
            display_name        VARCHAR NOT NULL,
            created_at          TIMESTAMP NOT NULL,
            CHECK (party_role IN (
                'primary_artist', 'featured', 'composer', 'producer', 'label'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_contributor_submission
        ON app_release_contributor(submission_id)
    """)


def _create_release_review(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_review (
            id              INTEGER PRIMARY KEY,
            submission_id   INTEGER NOT NULL,
            reviewer_id     INTEGER NOT NULL,
            decision        VARCHAR NOT NULL DEFAULT 'pending',
            notes           VARCHAR,
            created_at      TIMESTAMP NOT NULL,
            CHECK (decision IN (
                'pending', 'approve', 'reject', 'changes_requested',
                'suspend', 'withdraw'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_review_submission
        ON app_release_review(submission_id)
    """)


def _create_release_review_issue(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_review_issue (
            id              INTEGER PRIMARY KEY,
            review_id       INTEGER,
            submission_id   INTEGER NOT NULL,
            severity        VARCHAR NOT NULL,
            code            VARCHAR NOT NULL,
            message         VARCHAR NOT NULL,
            field_ref       VARCHAR,
            resolved        BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMP NOT NULL,
            CHECK (severity IN ('warn', 'block'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_review_issue_submission
        ON app_release_review_issue(submission_id)
    """)


def _create_release_status_history(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_status_history (
            id              INTEGER PRIMARY KEY,
            submission_id   INTEGER NOT NULL,
            from_status     VARCHAR NOT NULL,
            to_status       VARCHAR NOT NULL,
            actor_user_id   INTEGER NOT NULL,
            reason          VARCHAR,
            created_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_status_hist_submission
        ON app_release_status_history(submission_id)
    """)


def _create_release_publication(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_publication (
            id                      INTEGER PRIMARY KEY,
            submission_id           INTEGER NOT NULL,
            published_by            INTEGER NOT NULL,
            published_at            TIMESTAMP NOT NULL,
            version_label           VARCHAR,
            warehouse_track_ids_json VARCHAR,
            idempotency_key         VARCHAR NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_publication_submission
        ON app_release_publication(submission_id)
    """)


def _create_release_takedown(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_release_takedown (
            id              INTEGER PRIMARY KEY,
            submission_id   INTEGER NOT NULL,
            reason          VARCHAR NOT NULL,
            actor_user_id   INTEGER NOT NULL,
            kind            VARCHAR NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            CHECK (kind IN ('suspend', 'withdraw'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_release_takedown_submission
        ON app_release_takedown(submission_id)
    """)


def _create_media_asset(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_media_asset (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER NOT NULL,
            kind                VARCHAR NOT NULL,
            content_type        VARCHAR NOT NULL,
            original_filename   VARCHAR NOT NULL,
            stored_name         VARCHAR NOT NULL,
            relative_path       VARCHAR NOT NULL,
            byte_size           BIGINT NOT NULL,
            sha256              VARCHAR NOT NULL,
            duration_ms         INTEGER,
            width               INTEGER,
            height              INTEGER,
            status              VARCHAR NOT NULL DEFAULT 'private',
            created_by          INTEGER NOT NULL,
            created_at          TIMESTAMP NOT NULL,
            CHECK (kind IN ('audio', 'cover')),
            CHECK (status IN ('private', 'published', 'deleted'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_asset_org
        ON app_media_asset(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_asset_sha
        ON app_media_asset(organization_id, sha256)
    """)


def _create_media_upload(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_media_upload (
            id                  INTEGER PRIMARY KEY,
            media_asset_id      INTEGER NOT NULL,
            upload_status       VARCHAR NOT NULL DEFAULT 'received',
            rejection_reason    VARCHAR,
            created_at          TIMESTAMP NOT NULL,
            CHECK (upload_status IN ('received', 'validated', 'rejected'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_upload_asset
        ON app_media_upload(media_asset_id)
    """)


def _create_media_validation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_media_validation (
            id              INTEGER PRIMARY KEY,
            media_asset_id  INTEGER NOT NULL,
            check_code      VARCHAR NOT NULL,
            passed          BOOLEAN NOT NULL,
            detail          VARCHAR,
            created_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_media_validation_asset
        ON app_media_validation(media_asset_id)
    """)


def _create_duplicate_candidate(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_duplicate_candidate (
            id              INTEGER PRIMARY KEY,
            submission_id   INTEGER NOT NULL,
            track_id        INTEGER,
            match_type      VARCHAR NOT NULL,
            matched_ref     VARCHAR NOT NULL,
            severity        VARCHAR NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            CHECK (match_type IN ('hash', 'isrc', 'title_artist_duration')),
            CHECK (severity IN ('warn', 'block'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_dup_candidate_submission
        ON app_catalog_duplicate_candidate(submission_id)
    """)


def _create_publication_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_publication_event (
            id              INTEGER PRIMARY KEY,
            submission_id   INTEGER NOT NULL,
            event_type      VARCHAR NOT NULL,
            payload         VARCHAR,
            actor_user_id   INTEGER NOT NULL,
            created_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_pub_event_submission
        ON app_catalog_publication_event(submission_id)
    """)


def _create_artist_portal_access(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_portal_access (
            id                  INTEGER PRIMARY KEY,
            user_id             INTEGER NOT NULL,
            artist_profile_id   INTEGER NOT NULL,
            organization_id     INTEGER NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'active',
            created_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'revoked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_portal_user
        ON app_artist_portal_access(user_id, organization_id)
    """)
