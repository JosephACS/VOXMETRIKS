"""Billing schema — Spec 019.

Idempotent CREATE TABLE IF NOT EXISTS for all billing tables.
Call after ensure_subscription_tables and before mark_schema_ready.
NO PAN/CVV columns anywhere.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.billing.schema")

BILLING_TABLES = (
    "app_billing_profile",
    "app_invoice",
    "app_invoice_item",
    "app_payment_method_reference",
    "app_payment_attempt",
    "app_payment",
    "app_payment_allocation",
    "app_refund",
    "app_credit_note",
    "app_payment_provider_event",
    "app_billing_ledger_entry",
)


def ensure_billing_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all billing tables (idempotent)."""
    if schema_ready():
        return

    _create_billing_profile(conn)
    _create_invoice(conn)
    _create_invoice_item(conn)
    _create_payment_method_reference(conn)
    _create_payment_attempt(conn)
    _create_payment(conn)
    _create_payment_allocation(conn)
    _create_refund(conn)
    _create_credit_note(conn)
    _create_payment_provider_event(conn)
    _create_billing_ledger_entry(conn)

    logger.info("Billing schema ensured (%s tables)", len(BILLING_TABLES))


def _create_billing_profile(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_billing_profile (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL UNIQUE,
            default_currency VARCHAR(3) NOT NULL,
            legal_name       VARCHAR,
            tax_id           VARCHAR,
            billing_address  VARCHAR,
            email            VARCHAR,
            status           VARCHAR NOT NULL DEFAULT 'active',
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'suspended', 'closed'))
        )
    """)


def _create_invoice(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_invoice (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER NOT NULL,
            billing_profile_id  INTEGER NOT NULL,
            subscription_id     INTEGER,
            invoice_number      VARCHAR NOT NULL UNIQUE,
            currency            VARCHAR(3) NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            subtotal            DECIMAL(18,4) NOT NULL DEFAULT 0,
            total               DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount_paid         DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount_due          DECIMAL(18,4) NOT NULL DEFAULT 0,
            period_start        DATE,
            period_end          DATE,
            due_date            DATE,
            issued_at           TIMESTAMP,
            paid_at             TIMESTAMP,
            voided_at           TIMESTAMP,
            notes               VARCHAR,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN (
                'draft', 'issued', 'partially_paid', 'paid',
                'past_due', 'void', 'partially_credited', 'credited'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_invoice_org
        ON app_invoice(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_invoice_billing_profile
        ON app_invoice(billing_profile_id)
    """)


def _create_invoice_item(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_invoice_item (
            id            INTEGER PRIMARY KEY,
            invoice_id    INTEGER NOT NULL,
            description   VARCHAR NOT NULL,
            quantity      DECIMAL(18,4) NOT NULL DEFAULT 1,
            unit_price    DECIMAL(18,4) NOT NULL,
            amount        DECIMAL(18,4) NOT NULL,
            period_start  DATE,
            period_end    DATE,
            created_at    TIMESTAMP NOT NULL,
            CHECK (quantity > 0),
            CHECK (unit_price >= 0),
            CHECK (amount >= 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_invoice_item_invoice
        ON app_invoice_item(invoice_id)
    """)


def _create_payment_method_reference(conn: duckdb.DuckDBPyConnection) -> None:
    """Tokenized refs only — NO PAN/CVV columns."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payment_method_reference (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL,
            provider_code    VARCHAR NOT NULL,
            display_label    VARCHAR NOT NULL,
            token_ref        VARCHAR NOT NULL,
            method_type      VARCHAR NOT NULL,
            is_default       BOOLEAN NOT NULL DEFAULT FALSE,
            status           VARCHAR NOT NULL DEFAULT 'active',
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'removed')),
            CHECK (method_type IN ('card', 'bank_transfer', 'mock'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_method_org
        ON app_payment_method_reference(organization_id)
    """)


def _create_payment_attempt(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payment_attempt (
            id                      INTEGER PRIMARY KEY,
            organization_id         INTEGER NOT NULL,
            invoice_id              INTEGER NOT NULL,
            payment_method_ref_id   INTEGER,
            provider_code           VARCHAR NOT NULL,
            idempotency_key         VARCHAR NOT NULL UNIQUE,
            amount                  DECIMAL(18,4) NOT NULL,
            currency                VARCHAR(3) NOT NULL,
            status                  VARCHAR NOT NULL DEFAULT 'created',
            provider_attempt_id     VARCHAR,
            failure_reason          VARCHAR,
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (status IN ('created', 'processing', 'succeeded', 'failed', 'canceled')),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_attempt_invoice
        ON app_payment_attempt(invoice_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_attempt_org
        ON app_payment_attempt(organization_id)
    """)


def _create_payment(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payment (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER NOT NULL,
            payment_attempt_id  INTEGER NOT NULL,
            provider_code       VARCHAR NOT NULL,
            amount              DECIMAL(18,4) NOT NULL,
            currency            VARCHAR(3) NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'recorded',
            provider_payment_id VARCHAR,
            settled_at          TIMESTAMP,
            reconciled_at       TIMESTAMP,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN (
                'recorded', 'settled', 'reconciled',
                'partially_refunded', 'refunded', 'reversed'
            )),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_org
        ON app_payment(organization_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_attempt_fk
        ON app_payment(payment_attempt_id)
    """)


def _create_payment_allocation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payment_allocation (
            id               INTEGER PRIMARY KEY,
            payment_id       INTEGER NOT NULL,
            invoice_id       INTEGER NOT NULL,
            organization_id  INTEGER NOT NULL,
            amount           DECIMAL(18,4) NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_allocation_invoice
        ON app_payment_allocation(invoice_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_allocation_payment
        ON app_payment_allocation(payment_id)
    """)


def _create_refund(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_refund (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL,
            payment_id       INTEGER NOT NULL,
            amount           DECIMAL(18,4) NOT NULL,
            currency         VARCHAR(3) NOT NULL,
            reason           VARCHAR,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            processed_at     TIMESTAMP,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'processed', 'failed')),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_refund_payment
        ON app_refund(payment_id)
    """)


def _create_credit_note(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_credit_note (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER NOT NULL,
            invoice_id          INTEGER NOT NULL,
            credit_note_number  VARCHAR NOT NULL UNIQUE,
            amount              DECIMAL(18,4) NOT NULL,
            currency            VARCHAR(3) NOT NULL,
            reason              VARCHAR,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            issued_at           TIMESTAMP,
            applied_at          TIMESTAMP,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'issued', 'applied', 'voided')),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_credit_note_invoice
        ON app_credit_note(invoice_id)
    """)


def _create_payment_provider_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_payment_provider_event (
            id                INTEGER PRIMARY KEY,
            provider_code     VARCHAR NOT NULL,
            provider_event_id VARCHAR NOT NULL UNIQUE,
            event_type        VARCHAR NOT NULL,
            payload           VARCHAR,
            processed         BOOLEAN NOT NULL DEFAULT FALSE,
            processed_at      TIMESTAMP,
            created_at        TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_provider_event_provider
        ON app_payment_provider_event(provider_code)
    """)


def _create_billing_ledger_entry(conn: duckdb.DuckDBPyConnection) -> None:
    """Append-only ledger — no UPDATE/DELETE permitted at use-case layer."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_billing_ledger_entry (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL,
            entry_type       VARCHAR NOT NULL,
            reference_type   VARCHAR NOT NULL,
            reference_id     INTEGER NOT NULL,
            amount           DECIMAL(18,4) NOT NULL,
            currency         VARCHAR(3) NOT NULL,
            description      VARCHAR,
            created_at       TIMESTAMP NOT NULL,
            CHECK (entry_type IN (
                'invoice_issued', 'payment_received', 'refund_issued',
                'credit_note_applied', 'adjustment'
            )),
            CHECK (reference_type IN ('invoice', 'payment', 'refund', 'credit_note'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ledger_org
        ON app_billing_ledger_entry(organization_id)
    """)
