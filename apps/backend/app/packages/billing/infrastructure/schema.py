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
    "app_billing_dunning",
)


def ensure_billing_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all billing tables (idempotent)."""
    if schema_ready():
        # Additive: create any missing tables (IF NOT EXISTS) including dunning.
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
        _create_billing_dunning(conn)
        _apply_payment_method_additive_columns(conn)
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
    _create_billing_dunning(conn)
    _apply_payment_method_additive_columns(conn)

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


# Spec 052 — safe display/simulation metadata (nullable for legacy rows). Never PAN/CVV.
PAYMENT_METHOD_ADDITIVE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("brand", "VARCHAR"),
    ("last4", "VARCHAR"),
    ("exp_month", "INTEGER"),
    ("exp_year", "INTEGER"),
    ("simulation_token", "VARCHAR"),
)


def _table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [table],
    ).fetchone()
    return row is not None


def _add_missing_columns(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: tuple[tuple[str, str], ...],
) -> None:
    from app.core.database import get_table_columns

    if not _table_exists(conn, table):
        return
    existing = {c.lower() for c in get_table_columns(conn, table)}
    for name, sql_type in columns:
        if name.lower() in existing:
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
        logger.info("Billing schema: added %s.%s", table, name)


def _apply_payment_method_additive_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Spec 052 — idempotent nullable safe-card metadata on payment method refs."""
    _add_missing_columns(
        conn, "app_payment_method_reference", PAYMENT_METHOD_ADDITIVE_COLUMNS
    )


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
            brand            VARCHAR,
            last4            VARCHAR,
            exp_month        INTEGER,
            exp_year         INTEGER,
            simulation_token VARCHAR,
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
            idempotency_key  VARCHAR NOT NULL,
            UNIQUE (organization_id, idempotency_key),
            CHECK (status IN ('pending', 'processed', 'failed')),
            CHECK (amount > 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_refund_payment
        ON app_refund(payment_id)
    """)
    _ensure_refund_idempotency(conn)


def _refund_unique_constraints(
    conn: duckdb.DuckDBPyConnection,
) -> list[tuple[str, list[str]]]:
    """Return UNIQUE constraints on app_refund as (constraint_text, columns)."""
    try:
        rows = conn.execute(
            """
            SELECT constraint_text, constraint_column_names
            FROM duckdb_constraints()
            WHERE table_name = 'app_refund' AND constraint_type = 'UNIQUE'
            """
        ).fetchall()
    except Exception:
        return []
    out: list[tuple[str, list[str]]] = []
    for text, cols in rows:
        names = [str(c) for c in (cols or [])]
        out.append((str(text or ""), names))
    return out


def _has_global_idempotency_unique(conn: duckdb.DuckDBPyConnection) -> bool:
    """True when UNIQUE covers only idempotency_key (legacy global key)."""
    for _text, cols in _refund_unique_constraints(conn):
        if [c.lower() for c in cols] == ["idempotency_key"]:
            return True
    return False


def _has_org_scoped_idempotency_unique(conn: duckdb.DuckDBPyConnection) -> bool:
    """True when UNIQUE covers (organization_id, idempotency_key) in any order."""
    wanted = {"organization_id", "idempotency_key"}
    for _text, cols in _refund_unique_constraints(conn):
        if {c.lower() for c in cols} == wanted and len(cols) == 2:
            return True
    return False


def _rebuild_refund_org_scoped_unique(conn: duckdb.DuckDBPyConnection) -> None:
    """Atomically rebuild app_refund with UNIQUE(organization_id, idempotency_key)."""
    staging = "app_refund__org_scoped_mig"
    conn.execute(f"DROP TABLE IF EXISTS {staging}")
    conn.execute(f"""
        CREATE TABLE {staging} (
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
            idempotency_key  VARCHAR NOT NULL,
            UNIQUE (organization_id, idempotency_key),
            CHECK (status IN ('pending', 'processed', 'failed')),
            CHECK (amount > 0)
        )
    """)
    conn.execute(f"""
        INSERT INTO {staging} (
            id, organization_id, payment_id, amount, currency, reason, status,
            processed_at, created_at, updated_at, idempotency_key
        )
        SELECT
            id, organization_id, payment_id, amount, currency, reason, status,
            processed_at, created_at, updated_at, idempotency_key
        FROM app_refund
    """)
    before = int(conn.execute("SELECT COUNT(*) FROM app_refund").fetchone()[0])
    after = int(conn.execute(f"SELECT COUNT(*) FROM {staging}").fetchone()[0])
    if before != after:
        conn.execute(f"DROP TABLE IF EXISTS {staging}")
        raise RuntimeError(
            f"refund migration row-count mismatch: source={before} staging={after}"
        )
    conn.execute("DROP TABLE app_refund")
    conn.execute(f"ALTER TABLE {staging} RENAME TO app_refund")
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_refund_payment
        ON app_refund(payment_id)
    """)


def _ensure_refund_idempotency(conn: duckdb.DuckDBPyConnection) -> None:
    """Migrate app_refund to org-scoped UNIQUE(organization_id, idempotency_key).

    Legacy tables with ``idempotency_key … UNIQUE`` keep an internal DuckDB
    UNIQUE(idempotency_key) that cannot be dropped via guessed index names.
    Those tables are rebuilt atomically with no data loss.
    """
    from app.core.database import transactional

    try:
        cols = {str(row[0]) for row in conn.execute("DESCRIBE app_refund").fetchall()}
    except Exception:
        return

    with transactional(conn):
        if "idempotency_key" not in cols:
            conn.execute("ALTER TABLE app_refund ADD COLUMN idempotency_key VARCHAR")

        # Backfill NULLs before enforcing NOT NULL / UNIQUE.
        null_rows = conn.execute(
            "SELECT id FROM app_refund WHERE idempotency_key IS NULL"
        ).fetchall()
        for (rid,) in null_rows:
            conn.execute(
                "UPDATE app_refund SET idempotency_key = ? WHERE id = ?",
                [f"legacy-refund-{int(rid)}", int(rid)],
            )

        # Rebuild when a legacy global UNIQUE remains, or when the composite
        # UNIQUE is missing entirely.
        if _has_global_idempotency_unique(conn) or not _has_org_scoped_idempotency_unique(
            conn
        ):
            _rebuild_refund_org_scoped_unique(conn)

        # Secondary unique index (harmless when the table UNIQUE already exists).
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_refund_org_idempotency_key
            ON app_refund(organization_id, idempotency_key)
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


def _create_billing_dunning(conn: duckdb.DuckDBPyConnection) -> None:
    """Academic dunning / mora state for invoices (mock/manual only)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_billing_dunning (
            id                   INTEGER PRIMARY KEY,
            organization_id      INTEGER NOT NULL,
            invoice_id           INTEGER NOT NULL,
            subscription_id      INTEGER,
            status               VARCHAR NOT NULL DEFAULT 'open',
            retry_count          INTEGER NOT NULL DEFAULT 0,
            next_retry_at        TIMESTAMP,
            grace_until          TIMESTAMP,
            last_error_sanitized VARCHAR,
            last_attempt_id      INTEGER,
            retry_lock_token     VARCHAR,
            created_at           TIMESTAMP NOT NULL,
            updated_at           TIMESTAMP NOT NULL,
            CHECK (status IN (
                'open', 'grace', 'retry_in_progress', 'limited',
                'blocked', 'recovered', 'canceled'
            )),
            CHECK (retry_count >= 0)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_billing_dunning_invoice
        ON app_billing_dunning(invoice_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_billing_dunning_org
        ON app_billing_dunning(organization_id)
    """)
