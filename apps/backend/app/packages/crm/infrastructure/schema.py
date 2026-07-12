"""CRM schema — Spec 017.

Idempotent CREATE TABLE IF NOT EXISTS for all CRM tables.
Call ensure_platform_rbac_tables first (separate call from main.py).
No physical deletes of audited records (soft-delete only).
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.crm.schema")

CRM_TABLES = (
    "app_crm_prospect",
    "app_crm_contact",
    "app_crm_prospect_contact",
    "app_crm_opportunity",
    "app_crm_opportunity_stage_history",
    "app_crm_sales_activity",
    "app_crm_quotation",
    "app_crm_quotation_version",
    "app_crm_quotation_item",
    "app_crm_approval_request",
    "app_crm_customer_conversion",
)


def ensure_crm_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all CRM tables (idempotent)."""
    if schema_ready():
        return

    _create_prospect(conn)
    _create_contact(conn)
    _create_prospect_contact(conn)
    _create_opportunity(conn)
    _create_opportunity_stage_history(conn)
    _create_sales_activity(conn)
    _create_quotation(conn)
    _create_quotation_version(conn)
    _create_quotation_item(conn)
    _create_approval_request(conn)
    _create_customer_conversion(conn)

    logger.info("CRM schema ensured (%s tables)", len(CRM_TABLES))


def _create_prospect(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_prospect (
            id               INTEGER PRIMARY KEY,
            display_name     VARCHAR NOT NULL,
            company_name     VARCHAR,
            email            VARCHAR,
            phone            VARCHAR,
            source           VARCHAR,
            status           VARCHAR NOT NULL DEFAULT 'new',
            owner_user_id    INTEGER NOT NULL,
            organization_id  INTEGER,
            notes            VARCHAR,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            deleted_at       TIMESTAMP,
            CHECK (status IN (
                'new', 'contacted', 'qualified', 'disqualified', 'converted', 'lost'
            ))
        )
    """)
    # owner_user_id is immutable (no index update issues)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_prospect_owner
        ON app_crm_prospect(owner_user_id)
    """)
    # No index on mutable organization_id (changes on conversion — DuckDB ART limitation)


def _create_contact(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_contact (
            id               INTEGER PRIMARY KEY,
            full_name        VARCHAR NOT NULL,
            email            VARCHAR,
            email_normalized VARCHAR,
            phone            VARCHAR,
            company_name     VARCHAR,
            linked_user_id   INTEGER,
            created_by       INTEGER NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            deleted_at       TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_contact_email_norm
        ON app_crm_contact(email_normalized)
    """)


def _create_prospect_contact(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_prospect_contact (
            prospect_id       INTEGER NOT NULL,
            contact_id        INTEGER NOT NULL,
            is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
            is_decision_maker BOOLEAN NOT NULL DEFAULT FALSE,
            is_signatory      BOOLEAN NOT NULL DEFAULT FALSE,
            added_at          TIMESTAMP NOT NULL,
            PRIMARY KEY (prospect_id, contact_id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_prospect_contact_prospect
        ON app_crm_prospect_contact(prospect_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_prospect_contact_contact
        ON app_crm_prospect_contact(contact_id)
    """)


def _create_opportunity(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_opportunity (
            id                  INTEGER PRIMARY KEY,
            prospect_id         INTEGER NOT NULL,
            name                VARCHAR NOT NULL,
            description         VARCHAR,
            stage               VARCHAR NOT NULL DEFAULT 'qualification',
            probability         INTEGER NOT NULL DEFAULT 0,
            expected_value      DECIMAL(18,2),
            currency            VARCHAR,
            expected_close_date DATE,
            actual_close_date   DATE,
            outcome             VARCHAR,
            owner_user_id       INTEGER NOT NULL,
            organization_id     INTEGER,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            deleted_at          TIMESTAMP,
            CHECK (stage IN (
                'qualification', 'proposal', 'negotiation',
                'closed_won', 'closed_lost', 'canceled'
            )),
            CHECK (probability >= 0 AND probability <= 100)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_opportunity_prospect
        ON app_crm_opportunity(prospect_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_opportunity_owner
        ON app_crm_opportunity(owner_user_id)
    """)


def _create_opportunity_stage_history(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_opportunity_stage_history (
            id              INTEGER PRIMARY KEY,
            opportunity_id  INTEGER NOT NULL,
            from_stage      VARCHAR,
            to_stage        VARCHAR NOT NULL,
            actor_user_id   INTEGER NOT NULL,
            reason          VARCHAR,
            occurred_at     TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_opp_stage_history_opp
        ON app_crm_opportunity_stage_history(opportunity_id)
    """)


def _create_sales_activity(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_sales_activity (
            id              INTEGER PRIMARY KEY,
            activity_type   VARCHAR NOT NULL,
            subject         VARCHAR,
            body            VARCHAR,
            outcome         VARCHAR,
            prospect_id     INTEGER,
            contact_id      INTEGER,
            opportunity_id  INTEGER,
            actor_user_id   INTEGER NOT NULL,
            scheduled_at    TIMESTAMP,
            completed_at    TIMESTAMP,
            status          VARCHAR NOT NULL DEFAULT 'planned',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            deleted_at      TIMESTAMP,
            CHECK (activity_type IN ('call', 'email', 'meeting', 'note', 'demo', 'other')),
            CHECK (status IN ('planned', 'completed', 'canceled'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_activity_opportunity
        ON app_crm_sales_activity(opportunity_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_activity_prospect
        ON app_crm_sales_activity(prospect_id)
    """)


def _create_quotation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_quotation (
            id                  INTEGER PRIMARY KEY,
            opportunity_id      INTEGER NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            currency            VARCHAR NOT NULL,
            notes               VARCHAR,
            row_version         INTEGER NOT NULL DEFAULT 1,
            current_version_no  INTEGER NOT NULL DEFAULT 0,
            created_by          INTEGER NOT NULL,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            deleted_at          TIMESTAMP,
            CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'expired'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_quotation_opportunity
        ON app_crm_quotation(opportunity_id)
    """)


def _create_quotation_version(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_quotation_version (
            id                          INTEGER PRIMARY KEY,
            quotation_id                INTEGER NOT NULL,
            version_no                  INTEGER NOT NULL,
            status                      VARCHAR NOT NULL DEFAULT 'draft',
            subtotal                    DECIMAL(18,2) NOT NULL DEFAULT 0,
            discount_pct                DECIMAL(5,2) NOT NULL DEFAULT 0,
            discount_requires_approval  BOOLEAN NOT NULL DEFAULT FALSE,
            total                       DECIMAL(18,2) NOT NULL DEFAULT 0,
            notes                       VARCHAR,
            sent_at                     TIMESTAMP,
            accepted_at                 TIMESTAMP,
            rejected_at                 TIMESTAMP,
            is_immutable                BOOLEAN NOT NULL DEFAULT FALSE,
            created_by                  INTEGER NOT NULL,
            created_at                  TIMESTAMP NOT NULL,
            UNIQUE (quotation_id, version_no),
            CHECK (status IN ('draft', 'pending_approval', 'approved', 'sent', 'accepted', 'rejected'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_qv_quotation
        ON app_crm_quotation_version(quotation_id)
    """)


def _create_quotation_item(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_quotation_item (
            id                   INTEGER PRIMARY KEY,
            quotation_version_id INTEGER NOT NULL,
            description          VARCHAR NOT NULL,
            quantity             DECIMAL(12,4) NOT NULL DEFAULT 1,
            unit_price           DECIMAL(18,2) NOT NULL,
            discount_pct         DECIMAL(5,2) NOT NULL DEFAULT 0,
            line_total           DECIMAL(18,2) NOT NULL,
            plan_code            VARCHAR,
            sort_order           INTEGER NOT NULL DEFAULT 0,
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_qi_version
        ON app_crm_quotation_item(quotation_version_id)
    """)


def _create_approval_request(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_approval_request (
            id             INTEGER PRIMARY KEY,
            object_type    VARCHAR NOT NULL,
            object_id      INTEGER NOT NULL,
            reason         VARCHAR NOT NULL,
            threshold_ref  VARCHAR,
            status         VARCHAR NOT NULL DEFAULT 'pending',
            requested_by   INTEGER NOT NULL,
            reviewed_by    INTEGER,
            review_note    VARCHAR,
            requested_at   TIMESTAMP NOT NULL,
            reviewed_at    TIMESTAMP,
            created_at     TIMESTAMP NOT NULL,
            updated_at     TIMESTAMP NOT NULL,
            CHECK (object_type IN ('quotation_version', 'contract')),
            CHECK (status IN ('pending', 'approved', 'rejected', 'canceled'))
        )
    """)
    # No index on mutable `status` column — DuckDB ART indexes cannot handle
    # UPDATE on indexed values (same limitation as org status in schema 016).
    # idx_crm_approval_object is append-only (object_type/object_id never change).
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_approval_object
        ON app_crm_approval_request(object_type, object_id)
    """)


def _create_customer_conversion(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_crm_customer_conversion (
            id                     INTEGER PRIMARY KEY,
            opportunity_id         INTEGER NOT NULL,
            mode                   VARCHAR NOT NULL,
            status                 VARCHAR NOT NULL DEFAULT 'pending',
            organization_id        INTEGER,
            contact_id             INTEGER,
            signatory_user_id      INTEGER,
            claim_token_hash       VARCHAR,
            claim_token_expires_at TIMESTAMP,
            claim_consumed_at      TIMESTAMP,
            idempotency_key        VARCHAR UNIQUE,
            requested_by           INTEGER NOT NULL,
            completed_at           TIMESTAMP,
            failure_reason         VARCHAR,
            created_at             TIMESTAMP NOT NULL,
            updated_at             TIMESTAMP NOT NULL,
            CHECK (mode IN ('create_org', 'link_existing')),
            CHECK (status IN (
                'pending', 'awaiting_customer_claim', 'processing',
                'completed', 'failed', 'canceled'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crm_conversion_opportunity
        ON app_crm_customer_conversion(opportunity_id)
    """)
