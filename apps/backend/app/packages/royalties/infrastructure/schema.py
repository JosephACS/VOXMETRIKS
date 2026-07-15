"""Royalty schema — Spec 030.

Idempotent CREATE TABLE IF NOT EXISTS for all royalty / payout tables.
Additive only. Call after ensure_catalog_rights_tables.
No bank/PAN columns anywhere.
"""

from __future__ import annotations

import logging

import duckdb

logger = logging.getLogger("voxmetrik.royalties.schema")

ROYALTY_TABLES = (
    "app_royalty_revenue_pool",
    "app_royalty_revenue_source",
    "app_royalty_settlement_run",
    "app_royalty_asset_allocation",
    "app_royalty_party_allocation",
    "app_royalty_adjustment",
    "app_royalty_statement",
    "app_payout_batch",
    "app_payout_instruction",
    "app_payout_event",
    "app_payout_failure",
    "app_royalty_audit_event",
    "app_royalty_demo_stream_weight",
)


def ensure_royalty_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all royalty tables (idempotent, additive)."""
    _create_revenue_pool(conn)
    _create_revenue_source(conn)
    _create_settlement_run(conn)
    _create_asset_allocation(conn)
    _create_party_allocation(conn)
    _create_adjustment(conn)
    _create_statement(conn)
    _create_payout_batch(conn)
    _create_payout_instruction(conn)
    _create_payout_event(conn)
    _create_payout_failure(conn)
    _create_audit_event(conn)
    _create_demo_stream_weight(conn)
    logger.info("Royalty schema ensured (%s tables)", len(ROYALTY_TABLES))


def _create_revenue_pool(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_revenue_pool (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER,
            currency            VARCHAR(3) NOT NULL,
            period_start        DATE NOT NULL,
            period_end          DATE NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            attribution_method  VARCHAR NOT NULL DEFAULT 'PRO_RATA_STREAM_SHARE',
            total_amount        DECIMAL(18,4) NOT NULL DEFAULT 0,
            residual_amount     DECIMAL(18,4) NOT NULL DEFAULT 0,
            label               VARCHAR,
            is_demo             BOOLEAN NOT NULL DEFAULT FALSE,
            idempotency_key     VARCHAR NOT NULL UNIQUE,
            created_by          INTEGER NOT NULL,
            approved_by         INTEGER,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            approved_at         TIMESTAMP,
            CHECK (status IN (
                'draft', 'approved', 'processing', 'allocated', 'closed', 'canceled'
            )),
            CHECK (attribution_method IN (
                'PRO_RATA_STREAM_SHARE', 'MANUAL_ATTRIBUTION'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_pool_org
        ON app_royalty_revenue_pool(organization_id)
    """)


def _create_revenue_source(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_revenue_source (
            id                  INTEGER PRIMARY KEY,
            pool_id             INTEGER NOT NULL,
            source_kind         VARCHAR NOT NULL,
            source_payment_id   VARCHAR,
            source_invoice_id   VARCHAR,
            amount              DECIMAL(18,4) NOT NULL,
            currency            VARCHAR(3) NOT NULL,
            reason              VARCHAR,
            evidence_ref        VARCHAR,
            actor_user_id       INTEGER NOT NULL,
            organization_id     INTEGER,
            status              VARCHAR NOT NULL DEFAULT 'candidate',
            created_at          TIMESTAMP NOT NULL,
            CHECK (source_kind IN ('B2C_PERSONAL_PAYMENT', 'B2B_MANUAL')),
            CHECK (status IN ('candidate', 'approved', 'rejected')),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_source_pool
        ON app_royalty_revenue_source(pool_id)
    """)


def _create_settlement_run(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_settlement_run (
            id                  INTEGER PRIMARY KEY,
            pool_id             INTEGER NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            currency            VARCHAR(3) NOT NULL,
            gross_total         DECIMAL(18,4) NOT NULL DEFAULT 0,
            adjustment_total    DECIMAL(18,4) NOT NULL DEFAULT 0,
            net_total           DECIMAL(18,4) NOT NULL DEFAULT 0,
            block_conflict_id   INTEGER,
            idempotency_key     VARCHAR NOT NULL UNIQUE,
            created_by          INTEGER NOT NULL,
            approved_by         INTEGER,
            finalized_at        TIMESTAMP,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            block_reason        VARCHAR,
            CHECK (status IN (
                'draft', 'calculating', 'blocked', 'calculated',
                'under_review', 'approved', 'finalized', 'reversed'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_settlement_pool
        ON app_royalty_settlement_run(pool_id)
    """)


def _create_asset_allocation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_asset_allocation (
            id                   INTEGER PRIMARY KEY,
            settlement_run_id    INTEGER NOT NULL,
            asset_id             INTEGER NOT NULL,
            warehouse_track_id   INTEGER,
            valid_event_count    BIGINT NOT NULL DEFAULT 0,
            total_event_count    BIGINT NOT NULL DEFAULT 0,
            participation        DECIMAL(18,8) NOT NULL DEFAULT 0,
            attributable_amount  DECIMAL(18,4) NOT NULL DEFAULT 0,
            rights_contract_id   INTEGER,
            status               VARCHAR NOT NULL DEFAULT 'ok',
            block_reason         VARCHAR,
            created_at           TIMESTAMP NOT NULL,
            CHECK (status IN ('ok', 'blocked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_asset_alloc_run
        ON app_royalty_asset_allocation(settlement_run_id)
    """)


def _create_party_allocation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_party_allocation (
            id                   INTEGER PRIMARY KEY,
            settlement_run_id    INTEGER NOT NULL,
            asset_allocation_id  INTEGER NOT NULL,
            party_id             INTEGER NOT NULL,
            party_name           VARCHAR NOT NULL,
            ownership_percentage DECIMAL(18,4) NOT NULL,
            gross_amount         DECIMAL(18,4) NOT NULL DEFAULT 0,
            adjustment_amount    DECIMAL(18,4) NOT NULL DEFAULT 0,
            net_amount           DECIMAL(18,4) NOT NULL DEFAULT 0,
            rights_contract_id   INTEGER,
            status               VARCHAR NOT NULL DEFAULT 'ok',
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_party_alloc_run
        ON app_royalty_party_allocation(settlement_run_id)
    """)


def _create_adjustment(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_adjustment (
            id                   INTEGER PRIMARY KEY,
            settlement_run_id    INTEGER NOT NULL,
            party_allocation_id  INTEGER,
            amount               DECIMAL(18,4) NOT NULL,
            reason               VARCHAR NOT NULL,
            actor_user_id        INTEGER NOT NULL,
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_adjustment_run
        ON app_royalty_adjustment(settlement_run_id)
    """)


def _create_statement(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_statement (
            id                   INTEGER PRIMARY KEY,
            settlement_run_id    INTEGER NOT NULL,
            party_id             INTEGER NOT NULL,
            party_name           VARCHAR NOT NULL,
            period_start         DATE NOT NULL,
            period_end           DATE NOT NULL,
            currency             VARCHAR(3) NOT NULL,
            gross_amount         DECIMAL(18,4) NOT NULL DEFAULT 0,
            adjustment_amount    DECIMAL(18,4) NOT NULL DEFAULT 0,
            net_amount           DECIMAL(18,4) NOT NULL DEFAULT 0,
            status               VARCHAR NOT NULL DEFAULT 'draft',
            export_json          VARCHAR,
            created_at           TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'issued', 'paid_simulated'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_statement_run
        ON app_royalty_statement(settlement_run_id)
    """)


def _create_payout_batch(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payout_batch (
            id                   INTEGER PRIMARY KEY,
            settlement_run_id    INTEGER NOT NULL,
            status               VARCHAR NOT NULL DEFAULT 'pending',
            currency             VARCHAR(3) NOT NULL,
            total_amount         DECIMAL(18,4) NOT NULL DEFAULT 0,
            idempotency_key      VARCHAR NOT NULL UNIQUE,
            created_by           INTEGER NOT NULL,
            created_at           TIMESTAMP NOT NULL,
            updated_at           TIMESTAMP NOT NULL,
            CHECK (status IN (
                'pending', 'approved', 'processing', 'paid_simulated',
                'failed', 'canceled', 'reversed'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payout_batch_run
        ON app_payout_batch(settlement_run_id)
    """)


def _create_payout_instruction(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payout_instruction (
            id                   INTEGER PRIMARY KEY,
            batch_id             INTEGER NOT NULL,
            statement_id         INTEGER NOT NULL,
            party_id             INTEGER NOT NULL,
            amount               DECIMAL(18,4) NOT NULL,
            currency             VARCHAR(3) NOT NULL,
            destination_type     VARCHAR NOT NULL,
            destination_ref      VARCHAR NOT NULL,
            status               VARCHAR NOT NULL DEFAULT 'pending',
            idempotency_key      VARCHAR NOT NULL UNIQUE,
            created_at           TIMESTAMP NOT NULL,
            updated_at           TIMESTAMP NOT NULL,
            CHECK (destination_type IN (
                'demo_wallet', 'demo_bank_reference', 'simulated_account_token'
            )),
            CHECK (status IN (
                'pending', 'approved', 'processing', 'paid_simulated',
                'failed', 'canceled', 'reversed'
            )),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payout_instruction_batch
        ON app_payout_instruction(batch_id)
    """)


def _create_payout_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payout_event (
            id                   INTEGER PRIMARY KEY,
            instruction_id       INTEGER NOT NULL,
            event_type           VARCHAR NOT NULL,
            payload              VARCHAR,
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payout_event_instruction
        ON app_payout_event(instruction_id)
    """)


def _create_payout_failure(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payout_failure (
            id                   INTEGER PRIMARY KEY,
            instruction_id       INTEGER NOT NULL,
            failure_code         VARCHAR NOT NULL,
            message              VARCHAR NOT NULL,
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payout_failure_instruction
        ON app_payout_failure(instruction_id)
    """)


def _create_audit_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_audit_event (
            id                   INTEGER PRIMARY KEY,
            organization_id      INTEGER,
            actor_user_id        INTEGER NOT NULL,
            action               VARCHAR NOT NULL,
            entity_type          VARCHAR NOT NULL,
            entity_id            INTEGER NOT NULL,
            detail               VARCHAR,
            created_at           TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_audit_entity
        ON app_royalty_audit_event(entity_type, entity_id)
    """)


def _create_demo_stream_weight(conn: duckdb.DuckDBPyConnection) -> None:
    """Synthetic stream weights for testability without warehouse lock."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_royalty_demo_stream_weight (
            id                   INTEGER PRIMARY KEY,
            pool_id              INTEGER NOT NULL,
            track_id             INTEGER NOT NULL,
            event_count          BIGINT NOT NULL,
            is_synthetic         BOOLEAN NOT NULL DEFAULT TRUE,
            CHECK (event_count > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_royalty_demo_weight_pool
        ON app_royalty_demo_stream_weight(pool_id)
    """)
