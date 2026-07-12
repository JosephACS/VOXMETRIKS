"""Test L1: Billing schema — Spec 019.

Verifies:
- All 11 billing tables created.
- idempotency_key UNIQUE on app_payment_attempt.
- provider_event_id UNIQUE on app_payment_provider_event.
- NO PAN/CVV columns.
- Invoice status CHECK constraints enforced.
- Payment attempt status CHECK constraints enforced.
- billing.view / billing.manage permissions seeded in org catalogs.
"""

from __future__ import annotations

import pytest
import duckdb


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("billing_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


# ── Table existence ────────────────────────────────────────────────────────────

def test_billing_profile_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_billing_profile LIMIT 0")


def test_invoice_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_invoice LIMIT 0")


def test_invoice_item_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_invoice_item LIMIT 0")


def test_payment_method_reference_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_payment_method_reference LIMIT 0")


def test_payment_attempt_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_payment_attempt LIMIT 0")


def test_payment_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_payment LIMIT 0")


def test_payment_allocation_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_payment_allocation LIMIT 0")


def test_refund_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_refund LIMIT 0")


def test_credit_note_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_credit_note LIMIT 0")


def test_payment_provider_event_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_payment_provider_event LIMIT 0")


def test_billing_ledger_entry_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_billing_ledger_entry LIMIT 0")


# ── No PAN/CVV columns ─────────────────────────────────────────────────────────

def test_no_pan_column_anywhere(db_conn):
    """app_payment_method_reference must not contain pan, card_number, full_card, etc."""
    tables_to_check = [
        "app_payment_method_reference",
        "app_payment_attempt",
        "app_payment",
        "app_billing_profile",
    ]
    forbidden = {"pan", "card_number", "full_card", "cvv", "cvc", "expiry", "card_expiry"}
    for table in tables_to_check:
        cols = db_conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [table],
        ).fetchall()
        col_names = {str(r[0]).lower() for r in cols}
        for bad in forbidden:
            assert bad not in col_names, (
                f"Found forbidden column '{bad}' in {table}"
            )


# ── Unique constraints ─────────────────────────────────────────────────────────

def test_payment_attempt_idempotency_key_unique(db_conn):
    """Duplicate idempotency_key must raise."""
    from datetime import datetime
    from app.core.time_util import utc_now
    now = utc_now()
    db_conn.execute("""
        INSERT INTO app_payment_attempt
            (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
             idempotency_key, amount, currency, status, provider_attempt_id, failure_reason,
             created_at, updated_at)
        VALUES (9001, 1, 1, NULL, 'academic_mock', 'ik-test-unique-l1', 100.0, 'USD', 'created', NULL, NULL, ?, ?)
    """, [now, now])
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_payment_attempt
                (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
                 idempotency_key, amount, currency, status, provider_attempt_id, failure_reason,
                 created_at, updated_at)
            VALUES (9002, 1, 1, NULL, 'academic_mock', 'ik-test-unique-l1', 200.0, 'USD', 'created', NULL, NULL, ?, ?)
        """, [now, now])
    db_conn.execute("DELETE FROM app_payment_attempt WHERE id IN (9001, 9002)")


def test_provider_event_id_unique(db_conn):
    """Duplicate provider_event_id must raise."""
    from app.core.time_util import utc_now
    now = utc_now()
    db_conn.execute("""
        INSERT INTO app_payment_provider_event
            (id, provider_code, provider_event_id, event_type, payload, processed, processed_at, created_at)
        VALUES (8001, 'academic_mock', 'evt-l1-unique', 'payment.succeeded', NULL, TRUE, ?, ?)
    """, [now, now])
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_payment_provider_event
                (id, provider_code, provider_event_id, event_type, payload, processed, processed_at, created_at)
            VALUES (8002, 'academic_mock', 'evt-l1-unique', 'payment.succeeded', NULL, TRUE, ?, ?)
        """, [now, now])
    db_conn.execute("DELETE FROM app_payment_provider_event WHERE id IN (8001, 8002)")


# ── CHECK constraints ──────────────────────────────────────────────────────────

def test_invoice_status_check(db_conn):
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_invoice
                (id, organization_id, billing_profile_id, subscription_id, invoice_number,
                 currency, status, subtotal, total, amount_paid, amount_due,
                 period_start, period_end, due_date, issued_at, paid_at, voided_at,
                 notes, created_at, updated_at)
            VALUES (7001, 1, 1, NULL, 'INV-BAD', 'USD', 'invalid_status', 0, 0, 0, 0,
                    NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?)
        """, [now, now])


def test_payment_attempt_status_check(db_conn):
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_payment_attempt
                (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
                 idempotency_key, amount, currency, status, provider_attempt_id,
                 failure_reason, created_at, updated_at)
            VALUES (6001, 1, 1, NULL, 'academic_mock', 'ik-bad-status', 100.0, 'USD',
                    'invalid_status', NULL, NULL, ?, ?)
        """, [now, now])


def test_payment_method_no_method_type_check(db_conn):
    """method_type must be card/bank_transfer/mock."""
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_payment_method_reference
                (id, organization_id, provider_code, display_label, token_ref,
                 method_type, is_default, status, created_at, updated_at)
            VALUES (5001, 1, 'academic_mock', '••••1234', 'tok_xxx',
                    'unknown_type', FALSE, 'active', ?, ?)
        """, [now, now])


# ── Permissions seeded ─────────────────────────────────────────────────────────

def test_billing_view_permission_seeded(db_conn):
    row = db_conn.execute(
        "SELECT id FROM app_permission WHERE code = 'billing.view'"
    ).fetchone()
    assert row is not None, "billing.view permission not seeded"


def test_billing_manage_permission_seeded(db_conn):
    row = db_conn.execute(
        "SELECT id FROM app_permission WHERE code = 'billing.manage'"
    ).fetchone()
    assert row is not None, "billing.manage permission not seeded"


def test_invoice_create_permission_seeded(db_conn):
    row = db_conn.execute(
        "SELECT id FROM app_permission WHERE code = 'invoice.create'"
    ).fetchone()
    assert row is not None, "invoice.create permission not seeded"


def test_payment_manage_permission_seeded(db_conn):
    row = db_conn.execute(
        "SELECT id FROM app_permission WHERE code = 'payment.manage'"
    ).fetchone()
    assert row is not None, "payment.manage permission not seeded"


def test_owner_has_billing_permissions(db_conn):
    row = db_conn.execute(
        """
        SELECT 1
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'billing.manage'
        WHERE br.code = 'owner'
        LIMIT 1
        """
    ).fetchone()
    assert row is not None, "owner role missing billing.manage"


def test_billing_manager_has_invoice_create(db_conn):
    row = db_conn.execute(
        """
        SELECT 1
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'invoice.create'
        WHERE br.code = 'billing_manager'
        LIMIT 1
        """
    ).fetchone()
    assert row is not None, "billing_manager role missing invoice.create"


def test_finance_has_billing_view(db_conn):
    row = db_conn.execute(
        """
        SELECT 1
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'billing.view'
        WHERE br.code = 'finance'
        LIMIT 1
        """
    ).fetchone()
    assert row is not None, "finance role missing billing.view"


# ── Legacy subscription tables still present ──────────────────────────────────

def test_subscription_tables_still_present(db_conn):
    """Billing schema addition must not break subscription tables."""
    db_conn.execute("SELECT id FROM app_subscription LIMIT 0")
    db_conn.execute("SELECT id FROM app_plan LIMIT 0")
