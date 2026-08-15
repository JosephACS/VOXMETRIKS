"""Subscriptions schema — Spec 018 / Spec 052.

Idempotent CREATE TABLE IF NOT EXISTS for all subscription tables.
Call after ensure_platform_rbac_tables and ensure_organization_tables.
No invoice, payment, billing_profile, refund, credit_note tables.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.subscriptions.schema")

SUBSCRIPTION_TABLES = (
    "app_plan",
    "app_plan_price",
    "app_plan_feature",
    "app_addon",
    "app_subscription",
    "app_subscription_change",
    "app_subscription_entitlement",
    "app_subscription_addon",
    "app_usage_record",
    "app_subscription_access_state",
    "app_subscription_checkout_session",
)


def ensure_subscription_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all subscription tables (idempotent) and sync commercial catalog."""
    if schema_ready():
        # Additive IF NOT EXISTS for isolated DBs sharing process-level ready flag.
        _create_plan(conn)
        _create_plan_price(conn)
        _create_plan_feature(conn)
        _create_addon(conn)
        _create_subscription(conn)
        _create_subscription_change(conn)
        _create_subscription_entitlement(conn)
        _create_subscription_addon(conn)
        _create_usage_record(conn)
        _create_subscription_access_state(conn)
        _create_subscription_checkout_session(conn)
        _ensure_subscription_pending_status(conn)
    else:
        _create_plan(conn)
        _create_plan_price(conn)
        _create_plan_feature(conn)
        _create_addon(conn)
        _create_subscription(conn)
        _create_subscription_change(conn)
        _create_subscription_entitlement(conn)
        _create_subscription_addon(conn)
        _create_usage_record(conn)
        _create_subscription_access_state(conn)
        _create_subscription_checkout_session(conn)
        _ensure_subscription_pending_status(conn)
        logger.info("Subscriptions schema ensured (%s tables)", len(SUBSCRIPTION_TABLES))

    try:
        from app.packages.subscriptions.application.commercial_catalog import (
            ensure_commercial_catalog,
        )

        ensure_commercial_catalog(conn)
    except Exception as exc:  # noqa: BLE001 — catalog must not block schema
        logger.warning("commercial catalog ensure skipped: %s", exc.__class__.__name__)


def _create_plan(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_plan (
            id                  INTEGER PRIMARY KEY,
            code                VARCHAR NOT NULL UNIQUE,
            display_name        VARCHAR NOT NULL,
            description         VARCHAR,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            trial_days_default  INTEGER NOT NULL DEFAULT 0,
            sort_order          INTEGER NOT NULL DEFAULT 0,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'active', 'archived'))
        )
    """)
    # No index on mutable status column — DuckDB ART limitation


def _create_plan_price(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_plan_price (
            id              INTEGER PRIMARY KEY,
            plan_id         INTEGER NOT NULL,
            currency        VARCHAR NOT NULL,
            billing_period  VARCHAR NOT NULL,
            amount          DECIMAL(18,4) NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (billing_period IN ('monthly', 'annual', 'one_time')),
            CHECK (status IN ('active', 'retired')),
            CHECK (amount >= 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_plan_price_plan
        ON app_plan_price(plan_id)
    """)


def _create_plan_feature(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_plan_feature (
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
        CREATE INDEX IF NOT EXISTS idx_plan_feature_plan
        ON app_plan_feature(plan_id)
    """)


def _create_addon(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_addon (
            id              INTEGER PRIMARY KEY,
            code            VARCHAR NOT NULL UNIQUE,
            display_name    VARCHAR NOT NULL,
            description     VARCHAR,
            feature_code    VARCHAR,
            amount          DECIMAL(18,4),
            currency        VARCHAR,
            billing_period  VARCHAR,
            status          VARCHAR NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'retired'))
        )
    """)


def _create_subscription(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription (
            id                      INTEGER PRIMARY KEY,
            organization_id         INTEGER NOT NULL,
            plan_id                 INTEGER NOT NULL,
            plan_price_id           INTEGER,
            status                  VARCHAR NOT NULL DEFAULT 'trialing',
            billing_currency        VARCHAR NOT NULL,
            trial_ends_at           TIMESTAMP,
            current_period_start    DATE,
            current_period_end      DATE,
            cancel_at_period_end    BOOLEAN NOT NULL DEFAULT FALSE,
            canceled_at             TIMESTAMP,
            activation_source       VARCHAR,
            access_state            VARCHAR NOT NULL DEFAULT 'full',
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (status IN (
                'pending', 'trialing', 'active', 'past_due', 'canceled', 'expired'
            )),
            CHECK (access_state IN ('full', 'limited', 'blocked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscription_org
        ON app_subscription(organization_id)
    """)


def _subscription_status_allows_pending(conn: duckdb.DuckDBPyConnection) -> bool:
    """True when CHECK on status already includes 'pending'."""
    try:
        rows = conn.execute(
            """
            SELECT constraint_text
            FROM duckdb_constraints()
            WHERE table_name = 'app_subscription' AND constraint_type = 'CHECK'
            """
        ).fetchall()
    except Exception:
        return False
    for (text,) in rows:
        t = str(text or "").lower()
        if "status" in t and "pending" in t:
            return True
    return False


def _rebuild_subscription_with_pending(conn: duckdb.DuckDBPyConnection) -> None:
    """Atomically rebuild app_subscription CHECK to include status='pending'."""
    staging = "app_subscription__pending_mig"
    conn.execute(f"DROP TABLE IF EXISTS {staging}")
    conn.execute(f"""
        CREATE TABLE {staging} (
            id                      INTEGER PRIMARY KEY,
            organization_id         INTEGER NOT NULL,
            plan_id                 INTEGER NOT NULL,
            plan_price_id           INTEGER,
            status                  VARCHAR NOT NULL DEFAULT 'trialing',
            billing_currency        VARCHAR NOT NULL,
            trial_ends_at           TIMESTAMP,
            current_period_start    DATE,
            current_period_end      DATE,
            cancel_at_period_end    BOOLEAN NOT NULL DEFAULT FALSE,
            canceled_at             TIMESTAMP,
            activation_source       VARCHAR,
            access_state            VARCHAR NOT NULL DEFAULT 'full',
            created_at              TIMESTAMP NOT NULL,
            updated_at              TIMESTAMP NOT NULL,
            CHECK (status IN (
                'pending', 'trialing', 'active', 'past_due', 'canceled', 'expired'
            )),
            CHECK (access_state IN ('full', 'limited', 'blocked'))
        )
    """)
    conn.execute(f"""
        INSERT INTO {staging} (
            id, organization_id, plan_id, plan_price_id, status, billing_currency,
            trial_ends_at, current_period_start, current_period_end,
            cancel_at_period_end, canceled_at, activation_source, access_state,
            created_at, updated_at
        )
        SELECT
            id, organization_id, plan_id, plan_price_id, status, billing_currency,
            trial_ends_at, current_period_start, current_period_end,
            cancel_at_period_end, canceled_at, activation_source, access_state,
            created_at, updated_at
        FROM app_subscription
    """)
    before = int(conn.execute("SELECT COUNT(*) FROM app_subscription").fetchone()[0])
    after = int(conn.execute(f"SELECT COUNT(*) FROM {staging}").fetchone()[0])
    if before != after:
        conn.execute(f"DROP TABLE IF EXISTS {staging}")
        raise RuntimeError(
            f"subscription migration row-count mismatch: source={before} staging={after}"
        )
    conn.execute("DROP TABLE app_subscription")
    conn.execute(f"ALTER TABLE {staging} RENAME TO app_subscription")
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscription_org
        ON app_subscription(organization_id)
    """)
    logger.info("app_subscription rebuilt to allow status=pending")


def _ensure_subscription_pending_status(conn: duckdb.DuckDBPyConnection) -> None:
    """Migrate legacy app_subscription CHECK to include pending (Spec 052)."""
    from app.core.database import transactional

    try:
        conn.execute("SELECT 1 FROM app_subscription LIMIT 0")
    except Exception:
        return
    if _subscription_status_allows_pending(conn):
        return
    with transactional(conn):
        if not _subscription_status_allows_pending(conn):
            _rebuild_subscription_with_pending(conn)


def _create_subscription_change(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription_change (
            id               INTEGER PRIMARY KEY,
            subscription_id  INTEGER NOT NULL,
            change_type      VARCHAR NOT NULL,
            from_plan_id     INTEGER,
            to_plan_id       INTEGER,
            from_price_id    INTEGER,
            to_price_id      INTEGER,
            scheduled_for    DATE,
            applied_at       TIMESTAMP,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            actor_user_id    INTEGER NOT NULL,
            reason           VARCHAR,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (change_type IN (
                'upgrade', 'downgrade', 'addon_add', 'addon_remove',
                'cancel', 'reactivate', 'renew', 'trial_start', 'activate'
            )),
            CHECK (status IN ('pending', 'applied', 'canceled'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sub_change_subscription
        ON app_subscription_change(subscription_id)
    """)


def _create_subscription_entitlement(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription_entitlement (
            id               INTEGER PRIMARY KEY,
            subscription_id  INTEGER NOT NULL,
            feature_code     VARCHAR NOT NULL,
            source           VARCHAR NOT NULL DEFAULT 'plan',
            limit_value      INTEGER,
            enabled          BOOLEAN NOT NULL DEFAULT TRUE,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (source IN ('plan', 'addon', 'override'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sub_entitlement_subscription
        ON app_subscription_entitlement(subscription_id)
    """)


def _create_subscription_addon(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription_addon (
            id               INTEGER PRIMARY KEY,
            subscription_id  INTEGER NOT NULL,
            addon_id         INTEGER NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'active',
            added_at         TIMESTAMP NOT NULL,
            removed_at       TIMESTAMP,
            CHECK (status IN ('active', 'removed'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sub_addon_subscription
        ON app_subscription_addon(subscription_id)
    """)


def _create_usage_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_usage_record (
            id               INTEGER PRIMARY KEY,
            subscription_id  INTEGER NOT NULL,
            organization_id  INTEGER NOT NULL,
            feature_code     VARCHAR NOT NULL,
            quantity         DECIMAL(18,4) NOT NULL,
            period_start     DATE NOT NULL,
            period_end       DATE NOT NULL,
            idempotency_key  VARCHAR UNIQUE,
            recorded_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_usage_subscription
        ON app_usage_record(subscription_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_usage_org_feature
        ON app_usage_record(organization_id, feature_code)
    """)


def _create_subscription_access_state(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription_access_state (
            id               INTEGER PRIMARY KEY,
            subscription_id  INTEGER NOT NULL UNIQUE,
            access_state     VARCHAR NOT NULL DEFAULT 'full',
            reason           VARCHAR,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (access_state IN ('full', 'limited', 'blocked'))
        )
    """)


def _create_subscription_checkout_session(conn: duckdb.DuckDBPyConnection) -> None:
    """Organization checkout sessions — Spec 052. Safe metadata only; no PAN/CVV."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_subscription_checkout_session (
            id                      INTEGER PRIMARY KEY,
            organization_id         INTEGER NOT NULL,
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
            UNIQUE (organization_id, idempotency_key)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sub_checkout_org
        ON app_subscription_checkout_session(organization_id)
    """)
