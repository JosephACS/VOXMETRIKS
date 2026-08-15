"""Personal music subscriptions schema — Spec 029.

Additive CREATE TABLE IF NOT EXISTS. Completely separate from B2B
``app_subscription`` / ``app_invoice`` (organization_id owned).
Personal tables are always owned by ``user_id`` (owner_type = user).
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.personal_subscriptions.schema")

PERSONAL_SUBSCRIPTION_TABLES = (
    "personal_plan",
    "personal_plan_price",
    "personal_plan_feature",
    "personal_subscription",
    "household",
    "household_member",
    "household_invitation",
    "personal_invoice",
    "personal_invoice_item",
    "personal_payment_attempt",
    "personal_entitlement",
    "personal_subscription_event",
)


def ensure_personal_subscription_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create personal subscription tables (idempotent) and sync catalog."""
    _create_personal_plan(conn)
    _create_personal_plan_price(conn)
    _create_personal_plan_feature(conn)
    _create_personal_subscription(conn)
    _create_household(conn)
    _create_household_member(conn)
    _create_household_invitation(conn)
    _create_personal_invoice(conn)
    _create_personal_invoice_item(conn)
    _create_personal_payment_attempt(conn)
    _create_personal_entitlement(conn)
    _create_personal_subscription_event(conn)
    _create_personal_payment_method_reference(conn)
    _create_personal_checkout_session(conn)

    if not schema_ready():
        logger.info(
            "Personal subscriptions schema ensured (%s tables)",
            len(PERSONAL_SUBSCRIPTION_TABLES) + 2,
        )

    try:
        from app.packages.personal_subscriptions.application.catalog import (
            ensure_personal_catalog,
        )

        ensure_personal_catalog(conn)
    except Exception as exc:  # noqa: BLE001 — catalog must not block schema
        logger.warning("personal catalog ensure skipped: %s", exc.__class__.__name__)


def _create_personal_plan(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_plan (
            id                  INTEGER PRIMARY KEY,
            code                VARCHAR NOT NULL UNIQUE,
            display_name        VARCHAR NOT NULL,
            description         VARCHAR,
            status              VARCHAR NOT NULL DEFAULT 'active',
            max_members         INTEGER NOT NULL DEFAULT 1,
            sort_order          INTEGER NOT NULL DEFAULT 0,
            is_free             BOOLEAN NOT NULL DEFAULT FALSE,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'active', 'archived')),
            CHECK (max_members >= 1)
        )
    """)


def _create_personal_plan_price(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_plan_price (
            id              INTEGER PRIMARY KEY,
            plan_id         INTEGER NOT NULL,
            currency        VARCHAR NOT NULL DEFAULT 'USD',
            billing_period  VARCHAR NOT NULL,
            amount          DECIMAL(18,4) NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (billing_period IN ('monthly', 'annual')),
            CHECK (status IN ('active', 'retired')),
            CHECK (amount >= 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_plan_price_plan
        ON personal_plan_price(plan_id)
    """)


def _create_personal_plan_feature(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_plan_feature (
            id            INTEGER PRIMARY KEY,
            plan_id       INTEGER NOT NULL,
            feature_code  VARCHAR NOT NULL,
            limit_value   INTEGER,
            enabled       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_plan_feature_plan
        ON personal_plan_feature(plan_id)
    """)


def _create_personal_subscription(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_subscription (
            id                      INTEGER PRIMARY KEY,
            user_id                 INTEGER NOT NULL,
            plan_id                 INTEGER NOT NULL,
            plan_price_id           INTEGER,
            household_id            INTEGER,
            owner_type              VARCHAR NOT NULL DEFAULT 'user',
            status                  VARCHAR NOT NULL DEFAULT 'active',
            billing_currency        VARCHAR NOT NULL DEFAULT 'USD',
            current_period_start    DATE,
            current_period_end      DATE,
            cancel_at_period_end    BOOLEAN NOT NULL DEFAULT FALSE,
            canceled_at             TIMESTAMP,
            grace_until             TIMESTAMP,
            access_state            VARCHAR NOT NULL DEFAULT 'full',
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (owner_type = 'user'),
            CHECK (status IN (
                'active', 'past_due', 'canceled', 'expired', 'processing'
            )),
            CHECK (access_state IN ('full', 'limited', 'blocked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_sub_user
        ON personal_subscription(user_id)
    """)


def _create_household(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS household (
            id              INTEGER PRIMARY KEY,
            owner_user_id   INTEGER NOT NULL,
            plan_code       VARCHAR NOT NULL,
            max_members     INTEGER NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'canceled', 'closed')),
            CHECK (max_members IN (2, 6))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_household_owner
        ON household(owner_user_id)
    """)


def _create_household_member(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS household_member (
            id              INTEGER PRIMARY KEY,
            household_id    INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            role            VARCHAR NOT NULL DEFAULT 'member',
            status          VARCHAR NOT NULL DEFAULT 'active',
            joined_at       TIMESTAMP NOT NULL,
            left_at         TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (role IN ('owner', 'member')),
            CHECK (status IN ('active', 'removed', 'left'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_household_member_hh
        ON household_member(household_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_household_member_user
        ON household_member(user_id)
    """)


def _create_household_invitation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS household_invitation (
            id                  INTEGER PRIMARY KEY,
            household_id        INTEGER NOT NULL,
            email_normalized    VARCHAR NOT NULL,
            invited_by_user_id  INTEGER NOT NULL,
            token_hash          VARCHAR NOT NULL UNIQUE,
            status              VARCHAR NOT NULL DEFAULT 'pending',
            expires_at          TIMESTAMP NOT NULL,
            accepted_at         TIMESTAMP,
            accepted_by_user_id INTEGER,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'accepted', 'canceled', 'expired', 'revoked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_household_invite_hh
        ON household_invitation(household_id)
    """)


def _create_personal_invoice(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_invoice (
            id                      INTEGER PRIMARY KEY,
            user_id                 INTEGER NOT NULL,
            personal_subscription_id INTEGER,
            invoice_number          VARCHAR NOT NULL UNIQUE,
            currency                VARCHAR(3) NOT NULL DEFAULT 'USD',
            status                  VARCHAR NOT NULL DEFAULT 'draft',
            subtotal                DECIMAL(18,4) NOT NULL DEFAULT 0,
            total                   DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount_paid             DECIMAL(18,4) NOT NULL DEFAULT 0,
            amount_due              DECIMAL(18,4) NOT NULL DEFAULT 0,
            period_start            DATE,
            period_end              DATE,
            due_date                DATE,
            issued_at               TIMESTAMP,
            paid_at                 TIMESTAMP,
            voided_at               TIMESTAMP,
            notes                   VARCHAR,
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (status IN (
                'draft', 'issued', 'partially_paid', 'paid',
                'past_due', 'void', 'refunded'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_invoice_user
        ON personal_invoice(user_id)
    """)


def _create_personal_invoice_item(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_invoice_item (
            id                  INTEGER PRIMARY KEY,
            invoice_id          INTEGER NOT NULL,
            description         VARCHAR NOT NULL,
            quantity            INTEGER NOT NULL DEFAULT 1,
            unit_price          DECIMAL(18,4) NOT NULL,
            amount              DECIMAL(18,4) NOT NULL,
            created_at          TIMESTAMP NOT NULL
        )
    """)


def _create_personal_payment_attempt(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_payment_attempt (
            id              INTEGER PRIMARY KEY,
            invoice_id      INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            amount          DECIMAL(18,4) NOT NULL,
            currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
            status          VARCHAR NOT NULL DEFAULT 'created',
            provider_code   VARCHAR NOT NULL DEFAULT 'mock',
            is_mock         BOOLEAN NOT NULL DEFAULT TRUE,
            idempotency_key VARCHAR NOT NULL UNIQUE,
            scenario        VARCHAR,
            error_code      VARCHAR,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN (
                'created', 'processing', 'succeeded', 'failed', 'canceled'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_attempt_invoice
        ON personal_payment_attempt(invoice_id)
    """)


def _create_personal_entitlement(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_entitlement (
            id                      INTEGER PRIMARY KEY,
            personal_subscription_id INTEGER NOT NULL,
            user_id                 INTEGER NOT NULL,
            feature_code            VARCHAR NOT NULL,
            limit_value             INTEGER,
            enabled                 BOOLEAN NOT NULL DEFAULT TRUE,
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_entitlement_user
        ON personal_entitlement(user_id)
    """)


def _create_personal_subscription_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_subscription_event (
            id                      INTEGER PRIMARY KEY,
            personal_subscription_id INTEGER,
            user_id                 INTEGER NOT NULL,
            event_type              VARCHAR NOT NULL,
            payload_json            VARCHAR,
            actor_user_id           INTEGER,
            created_at              TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_sub_event_user
        ON personal_subscription_event(user_id)
    """)


def _create_personal_payment_method_reference(conn: duckdb.DuckDBPyConnection) -> None:
    """Safe tokenized refs only — NO PAN/CVV columns (Spec 052)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_payment_method_reference (
            id                  INTEGER PRIMARY KEY,
            user_id             INTEGER NOT NULL,
            provider_code       VARCHAR NOT NULL DEFAULT 'mock',
            brand               VARCHAR NOT NULL,
            last4               VARCHAR NOT NULL,
            exp_month           INTEGER NOT NULL,
            exp_year            INTEGER NOT NULL,
            display_label       VARCHAR NOT NULL,
            token_ref           VARCHAR NOT NULL,
            simulation_token    VARCHAR NOT NULL,
            is_default          BOOLEAN NOT NULL DEFAULT FALSE,
            status              VARCHAR NOT NULL DEFAULT 'active',
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'removed')),
            CHECK (length(last4) = 4)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_pm_user
        ON personal_payment_method_reference(user_id)
    """)


def _create_personal_checkout_session(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS personal_checkout_session (
            id                      INTEGER PRIMARY KEY,
            user_id                 INTEGER NOT NULL,
            actor_user_id           INTEGER NOT NULL,
            plan_code               VARCHAR NOT NULL,
            plan_id                 INTEGER NOT NULL,
            plan_price_id           INTEGER NOT NULL,
            billing_period          VARCHAR NOT NULL,
            amount                  DECIMAL(18,4) NOT NULL,
            currency                VARCHAR(3) NOT NULL DEFAULT 'USD',
            status                  VARCHAR NOT NULL DEFAULT 'draft',
            subscription_id         INTEGER,
            invoice_id              INTEGER,
            payment_attempt_id      INTEGER,
            payment_method_id       INTEGER,
            idempotency_key         VARCHAR NOT NULL,
            failure_code            VARCHAR,
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            expires_at              TIMESTAMP,
            completed_at            TIMESTAMP,
            CHECK (billing_period IN ('monthly', 'annual')),
            CHECK (status IN (
                'draft', 'awaiting_method', 'ready', 'processing',
                'succeeded', 'failed', 'canceled', 'expired'
            )),
            UNIQUE (user_id, idempotency_key)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_personal_checkout_user
        ON personal_checkout_session(user_id)
    """)
