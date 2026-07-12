"""Artists schema — Spec 020.

Idempotent CREATE TABLE IF NOT EXISTS for all artists tables.
Call after ensure_billing_tables and before mark_schema_ready.

app_artist_profile is the *business* artist record (organization-scoped),
kept fully distinct from the analytics warehouse dim_artista table.
warehouse_artist_id is an optional, non-enforced reference (no FK — DuckDB
does not enforce cross-domain FKs here and the warehouse is out of scope
for destructive changes).

NOTE ON UNIQUENESS: (organization_id, normalized_name), (artist_id, organization_id)
and (artist_id, system_code) natural-key uniqueness is enforced at the
application layer (use_cases.py) rather than via SQL UNIQUE constraints.

NOTE ON UPDATE vs DELETE+INSERT (DuckDB known limitation): DuckDB can, under
certain connection open/close/reopen sequences and/or in combination with a
secondary index, raise a spurious PRIMARY KEY ConstraintException on UPDATE
even when no duplicate row exists (see https://duckdb.org/docs/sql/indexes
— "known index limitations"). This has been observed on app_artist_profile
UPDATEs (status transitions, LinkWarehouseArtist, TransferArtistOrganization).
use_cases.py works around it via `_update_profile_row`, which applies these
field mutations as an atomic DELETE + re-INSERT of the same row (id
preserved) instead of a raw UPDATE. See accepted-debt.md for details.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.artists.schema")

ARTISTS_TABLES = (
    "app_artist_profile",
    "app_artist_organization",
    "app_artist_assignment",
    "app_artist_team_member",
    "app_artist_external_identifier",
    "app_artist_status_history",
)


def ensure_artist_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all artists tables (idempotent)."""
    if schema_ready():
        return

    _create_artist_profile(conn)
    _create_artist_organization(conn)
    _create_artist_assignment(conn)
    _create_artist_team_member(conn)
    _create_artist_external_identifier(conn)
    _create_artist_status_history(conn)

    logger.info("Artists schema ensured (%s tables)", len(ARTISTS_TABLES))


def _create_artist_profile(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_profile (
            id                    INTEGER PRIMARY KEY,
            organization_id       INTEGER NOT NULL,
            display_name          VARCHAR NOT NULL,
            legal_name            VARCHAR,
            normalized_name       VARCHAR NOT NULL,
            status                VARCHAR NOT NULL DEFAULT 'draft',
            warehouse_artist_id   INTEGER,
            created_by            INTEGER,
            created_at            TIMESTAMP NOT NULL,
            updated_at            TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'active', 'inactive', 'archived'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_profile_org
        ON app_artist_profile(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_profile_normalized_name
        ON app_artist_profile(normalized_name)
    """)


def _create_artist_organization(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_organization (
            id                  INTEGER PRIMARY KEY,
            artist_id           INTEGER NOT NULL,
            organization_id     INTEGER NOT NULL,
            relationship_role   VARCHAR NOT NULL DEFAULT 'secondary',
            is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
            status              VARCHAR NOT NULL DEFAULT 'active',
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (relationship_role IN ('primary', 'secondary', 'licensed', 'partner')),
            CHECK (status IN ('active', 'ended'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_org_artist
        ON app_artist_organization(artist_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_org_org
        ON app_artist_organization(organization_id)
    """)


def _create_artist_assignment(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_assignment (
            id               INTEGER PRIMARY KEY,
            artist_id        INTEGER NOT NULL,
            organization_id  INTEGER NOT NULL,
            user_id          INTEGER NOT NULL,
            role             VARCHAR NOT NULL DEFAULT 'manager',
            status           VARCHAR NOT NULL DEFAULT 'active',
            assigned_at      TIMESTAMP NOT NULL,
            ended_at         TIMESTAMP,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'ended'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_assignment_artist
        ON app_artist_assignment(artist_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_assignment_org
        ON app_artist_assignment(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_assignment_user
        ON app_artist_assignment(user_id)
    """)


def _create_artist_team_member(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_team_member (
            id               INTEGER PRIMARY KEY,
            artist_id        INTEGER NOT NULL,
            organization_id  INTEGER NOT NULL,
            user_id          INTEGER NOT NULL,
            team_role        VARCHAR NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'active',
            added_at         TIMESTAMP NOT NULL,
            removed_at       TIMESTAMP,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'removed'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_team_artist
        ON app_artist_team_member(artist_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_team_user
        ON app_artist_team_member(user_id)
    """)


def _create_artist_external_identifier(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_external_identifier (
            id               INTEGER PRIMARY KEY,
            artist_id        INTEGER NOT NULL,
            system_code      VARCHAR NOT NULL,
            external_value   VARCHAR NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_ext_id_artist
        ON app_artist_external_identifier(artist_id)
    """)


def _create_artist_status_history(conn: duckdb.DuckDBPyConnection) -> None:
    """Append-only status trail — inserted by use cases only."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_artist_status_history (
            id               INTEGER PRIMARY KEY,
            artist_id        INTEGER NOT NULL,
            organization_id  INTEGER NOT NULL,
            from_status      VARCHAR,
            to_status        VARCHAR NOT NULL,
            reason           VARCHAR,
            actor_user_id    INTEGER,
            at               TIMESTAMP NOT NULL,
            created_at       TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_artist_status_history_artist
        ON app_artist_status_history(artist_id)
    """)
