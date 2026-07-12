"""Catalog rights schema — Spec 021.

Idempotent CREATE TABLE IF NOT EXISTS for all catalog-rights tables.
Call after ensure_artist_tables and before mark_schema_ready.

app_catalog_asset / app_catalog_release are *business* records
(organization-scoped), kept fully distinct from the analytics warehouse
(dim_track / dim_album). warehouse_track_id / warehouse_album_id are
optional, non-enforced references (no FK — DuckDB does not enforce
cross-domain FKs here and the warehouse is out of scope for destructive
changes). dim_album does not currently exist as a physical table in this
warehouse; warehouse_album_id is stored purely as an opaque optional
reference with no existence check (see accepted-debt.md).

app_rights_contract is a *legal-rights* record (master/publishing/
neighboring/other), fully distinct from app_commercial_contract (Spec 017
CRM/commercial contracting, a sales agreement). The two tables are never
joined or merged.

NOTE ON UNIQUENESS: natural-key uniqueness (e.g. one active approval per
contract) is enforced at the application layer (use_cases.py) rather than
via SQL UNIQUE constraints, consistent with the artists (Spec 020) and
billing (Spec 019) packages.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.catalog_rights.schema")

CATALOG_RIGHTS_TABLES = (
    "app_catalog_asset",
    "app_catalog_release",
    "app_catalog_asset_artist",
    "app_catalog_ownership",
    "app_rights_contract",
    "app_rights_contract_party",
    "app_rights_territory",
    "app_rights_authorized_use",
    "app_rights_conflict",
    "app_rights_approval",
    "app_rights_status_history",
)


def ensure_catalog_rights_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all catalog-rights tables (idempotent)."""
    if schema_ready():
        return

    _create_catalog_asset(conn)
    _create_catalog_release(conn)
    _create_catalog_asset_artist(conn)
    _create_catalog_ownership(conn)
    _create_rights_contract(conn)
    _create_rights_contract_party(conn)
    _create_rights_territory(conn)
    _create_rights_authorized_use(conn)
    _create_rights_conflict(conn)
    _create_rights_approval(conn)
    _create_rights_status_history(conn)

    logger.info("Catalog rights schema ensured (%s tables)", len(CATALOG_RIGHTS_TABLES))


def _create_catalog_asset(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_asset (
            id                    INTEGER PRIMARY KEY,
            organization_id       INTEGER NOT NULL,
            title                 VARCHAR NOT NULL,
            status                VARCHAR NOT NULL DEFAULT 'draft',
            warehouse_track_id    INTEGER,
            artist_profile_id     INTEGER,
            created_by            INTEGER,
            created_at            TIMESTAMP NOT NULL,
            updated_at            TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'active', 'archived'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_asset_org
        ON app_catalog_asset(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_asset_artist
        ON app_catalog_asset(artist_profile_id)
    """)


def _create_catalog_release(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_release (
            id                    INTEGER PRIMARY KEY,
            organization_id       INTEGER NOT NULL,
            title                 VARCHAR NOT NULL,
            warehouse_album_id    INTEGER,
            created_by            INTEGER,
            created_at            TIMESTAMP NOT NULL,
            updated_at            TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_release_org
        ON app_catalog_release(organization_id)
    """)


def _create_catalog_asset_artist(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_asset_artist (
            id                  INTEGER PRIMARY KEY,
            asset_id            INTEGER NOT NULL,
            artist_profile_id   INTEGER NOT NULL,
            role                VARCHAR NOT NULL DEFAULT 'primary',
            created_at          TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_asset_artist_asset
        ON app_catalog_asset_artist(asset_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_asset_artist_artist
        ON app_catalog_asset_artist(artist_profile_id)
    """)


def _create_catalog_ownership(conn: duckdb.DuckDBPyConnection) -> None:
    """Descriptive org/artist ownership link — distinct from rights_contract_party
    percentage-of-rights bookkeeping. This records *who holds/administers* an
    asset in the catalog, not a legal percentage split."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_catalog_ownership (
            id                  INTEGER PRIMARY KEY,
            asset_id            INTEGER NOT NULL,
            organization_id     INTEGER,
            artist_profile_id   INTEGER,
            ownership_type      VARCHAR NOT NULL DEFAULT 'label',
            created_by          INTEGER,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (ownership_type IN ('label', 'artist', 'publisher', 'distributor', 'other'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalog_ownership_asset
        ON app_catalog_ownership(asset_id)
    """)


def _create_rights_contract(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_contract (
            id                INTEGER PRIMARY KEY,
            organization_id   INTEGER NOT NULL,
            asset_id          INTEGER NOT NULL,
            rights_type       VARCHAR NOT NULL,
            status            VARCHAR NOT NULL DEFAULT 'draft',
            exclusive         BOOLEAN NOT NULL DEFAULT FALSE,
            valid_from        DATE NOT NULL,
            valid_to          DATE,
            evidence_ref      VARCHAR,
            created_by        INTEGER,
            created_at        TIMESTAMP NOT NULL,
            updated_at        TIMESTAMP NOT NULL,
            CHECK (rights_type IN ('master', 'publishing', 'neighboring', 'other')),
            CHECK (status IN ('draft', 'active', 'expired', 'archived', 'disputed'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_contract_org
        ON app_rights_contract(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_contract_asset
        ON app_rights_contract(asset_id, rights_type)
    """)


def _create_rights_contract_party(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_contract_party (
            id                     INTEGER PRIMARY KEY,
            contract_id            INTEGER NOT NULL,
            party_name             VARCHAR NOT NULL,
            party_type             VARCHAR NOT NULL DEFAULT 'external',
            ownership_percentage   DOUBLE NOT NULL,
            organization_id        INTEGER,
            artist_profile_id      INTEGER,
            created_at             TIMESTAMP NOT NULL,
            updated_at             TIMESTAMP NOT NULL,
            CHECK (party_type IN ('organization', 'artist', 'external')),
            CHECK (ownership_percentage > 0 AND ownership_percentage <= 100)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_contract_party_contract
        ON app_rights_contract_party(contract_id)
    """)


def _create_rights_territory(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_territory (
            id               INTEGER PRIMARY KEY,
            contract_id      INTEGER NOT NULL,
            territory_code   VARCHAR NOT NULL,
            territory_name   VARCHAR NOT NULL,
            created_at       TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_territory_contract
        ON app_rights_territory(contract_id)
    """)


def _create_rights_authorized_use(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_authorized_use (
            id               INTEGER PRIMARY KEY,
            contract_id      INTEGER NOT NULL,
            use_code         VARCHAR NOT NULL,
            description      VARCHAR,
            created_at       TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_authorized_use_contract
        ON app_rights_authorized_use(contract_id)
    """)


def _create_rights_conflict(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_conflict (
            id                INTEGER PRIMARY KEY,
            organization_id   INTEGER NOT NULL,
            asset_id          INTEGER NOT NULL,
            rights_type       VARCHAR NOT NULL,
            territory_code    VARCHAR NOT NULL,
            status            VARCHAR NOT NULL DEFAULT 'open',
            details           VARCHAR,
            resolved_by       INTEGER,
            resolved_at       TIMESTAMP,
            created_at        TIMESTAMP NOT NULL,
            updated_at        TIMESTAMP NOT NULL,
            CHECK (status IN ('open', 'resolved', 'dismissed'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_conflict_asset
        ON app_rights_conflict(asset_id, rights_type, territory_code)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_conflict_org
        ON app_rights_conflict(organization_id)
    """)


def _create_rights_approval(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_approval (
            id                  INTEGER PRIMARY KEY,
            contract_id         INTEGER NOT NULL,
            organization_id     INTEGER NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'pending',
            approver_user_id    INTEGER,
            requested_by        INTEGER,
            notes               VARCHAR,
            decided_at          TIMESTAMP,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'approved', 'rejected'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_approval_contract
        ON app_rights_approval(contract_id)
    """)


def _create_rights_status_history(conn: duckdb.DuckDBPyConnection) -> None:
    """Append-only status trail across catalog-rights entities — inserted by
    use cases only (rights_contract, rights_conflict)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_rights_status_history (
            id                INTEGER PRIMARY KEY,
            organization_id   INTEGER NOT NULL,
            entity_type       VARCHAR NOT NULL,
            entity_id         INTEGER NOT NULL,
            from_status       VARCHAR,
            to_status         VARCHAR NOT NULL,
            actor             INTEGER,
            reason            VARCHAR,
            at                TIMESTAMP NOT NULL,
            created_at        TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rights_status_history_entity
        ON app_rights_status_history(entity_type, entity_id)
    """)
