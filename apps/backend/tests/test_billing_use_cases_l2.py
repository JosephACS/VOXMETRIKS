"""Test L2: Billing use cases — Spec 019.

Covers: CreateBillingProfile, IssueInvoice, VoidInvoice, CreatePaymentAttempt (idempotent),
        RecordManualPayment, AllocatePayment (partial/full), MarkInvoicePastDue,
        CreditNote, Ledger immutability.
"""

from __future__ import annotations

from decimal import Decimal

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("billing_uc") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)

    now = utc_now()
    # Seed a test organization
    conn.execute("""
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at)
        VALUES (100, 'Test Org L2', 'Test Org L2 LLC', 'test-org-l2', 'label', 'US',
                'UTC', 'USD', 'active', 1, ?, ?)
    """, [now, now])

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


ACTOR = 1
ORG = 100


# ── CreateBillingProfile ───────────────────────────────────────────────────────

def test_create_billing_profile(db_conn):
    from app.packages.billing.application.use_cases import BillingProfileUseCases

    profile = BillingProfileUseCases(db_conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        default_currency="USD",
        legal_name="Test Org L2 LLC",
        email="billing@testorg.com",
    )
    assert profile.organization_id == ORG
    assert profile.default_currency == "USD"
    assert profile.status == "active"


def test_create_billing_profile_duplicate_raises(db_conn):
    from app.packages.billing.application.use_cases import BillingProfileUseCases
    from app.packages.billing.domain.errors import BillingProfileExistsError

    with pytest.raises(BillingProfileExistsError):
        BillingProfileUseCases(db_conn).create(
            actor_user_id=ACTOR,
            organization_id=ORG,
            default_currency="USD",
        )


# ── IssueInvoice ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def billing_profile(db_conn):
    row = db_conn.execute(
        "SELECT id FROM app_billing_profile WHERE organization_id = ?", [ORG]
    ).fetchone()
    return int(row[0])


@pytest.fixture(scope="module")
def draft_invoice(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        billing_profile_id=billing_profile,
    )
    return inv


def test_create_invoice_draft(draft_invoice):
    assert draft_invoice.status == "draft"
    assert draft_invoice.total == Decimal("0")


def test_issue_invoice_without_items_raises(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import InvoiceUseCases
    from app.packages.billing.domain.errors import ValidationError

    with pytest.raises(ValidationError, match="no items"):
        InvoiceUseCases(db_conn).issue(
            draft_invoice.id,
            actor_user_id=ACTOR,
            organization_id=ORG,
        )


def test_add_invoice_item(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    item = InvoiceUseCases(db_conn).add_item(
        draft_invoice.id,
        actor_user_id=ACTOR,
        organization_id=ORG,
        description="Monthly subscription",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
    )
    assert item.amount == Decimal("100.00")


def test_invoice_total_computed_backend(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    inv = InvoiceUseCases(db_conn).get(draft_invoice.id, organization_id=ORG)
    assert inv.total == Decimal("100.00")


def test_issue_invoice_transitions_to_issued(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    inv = InvoiceUseCases(db_conn).issue(
        draft_invoice.id,
        actor_user_id=ACTOR,
        organization_id=ORG,
    )
    assert inv.status == "issued"
    assert inv.issued_at is not None


def test_add_item_to_issued_invoice_raises(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import InvoiceUseCases
    from app.packages.billing.domain.errors import InvoiceImmutableError

    with pytest.raises(InvoiceImmutableError):
        InvoiceUseCases(db_conn).add_item(
            draft_invoice.id,
            actor_user_id=ACTOR,
            organization_id=ORG,
            description="Blocked item",
            quantity=Decimal("1"),
            unit_price=Decimal("50.00"),
        )


# ── VoidInvoice ────────────────────────────────────────────────────────────────

def test_void_invoice(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        billing_profile_id=billing_profile,
    )
    voided = InvoiceUseCases(db_conn).void(
        inv.id, actor_user_id=ACTOR, organization_id=ORG, reason="test"
    )
    assert voided.status == "void"
    assert voided.voided_at is not None


# ── CreatePaymentAttempt idempotency ───────────────────────────────────────────

def test_payment_attempt_idempotent(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import PaymentAttemptUseCases

    attempt1 = PaymentAttemptUseCases(db_conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        invoice_id=draft_invoice.id,
        provider_code="academic_mock",
        idempotency_key="l2-idem-test-001",
        amount=Decimal("100.00"),
        currency="USD",
    )
    attempt2 = PaymentAttemptUseCases(db_conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        invoice_id=draft_invoice.id,
        provider_code="academic_mock",
        idempotency_key="l2-idem-test-001",
        amount=Decimal("100.00"),
        currency="USD",
    )
    assert attempt1.id == attempt2.id


# ── RecordManualPayment ────────────────────────────────────────────────────────

def test_record_manual_payment_creates_payment_and_ledger(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases, PaymentUseCases

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, billing_profile_id=billing_profile,
    )
    InvoiceUseCases(db_conn).add_item(
        inv.id, actor_user_id=ACTOR, organization_id=ORG,
        description="Service", quantity=Decimal("1"), unit_price=Decimal("200.00"),
    )
    InvoiceUseCases(db_conn).issue(inv.id, actor_user_id=ACTOR, organization_id=ORG)

    payment = PaymentUseCases(db_conn).record_manual(
        actor_user_id=ACTOR, organization_id=ORG,
        invoice_id=inv.id, amount=Decimal("200.00"), currency="USD",
        notes="Wire transfer ref #123",
    )
    assert payment.status == "recorded"
    assert payment.amount == Decimal("200.00")

    # Check ledger entry created
    count = db_conn.execute(
        "SELECT COUNT(*) FROM app_billing_ledger_entry WHERE reference_id = ? AND entry_type = 'payment_received'",
        [payment.id],
    ).fetchone()[0]
    assert int(count) >= 1

    # Invoice should be paid
    updated_inv = InvoiceUseCases(db_conn).get(inv.id, organization_id=ORG)
    assert updated_inv.status == "paid"


# ── Partial payment ────────────────────────────────────────────────────────────

def test_partial_payment_sets_partially_paid(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases, PaymentAttemptUseCases, PaymentUseCases
    from app.core.time_util import utc_now

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, billing_profile_id=billing_profile,
    )
    InvoiceUseCases(db_conn).add_item(
        inv.id, actor_user_id=ACTOR, organization_id=ORG,
        description="Large item", quantity=Decimal("1"), unit_price=Decimal("500.00"),
    )
    InvoiceUseCases(db_conn).issue(inv.id, actor_user_id=ACTOR, organization_id=ORG)

    payment = PaymentUseCases(db_conn).record_manual(
        actor_user_id=ACTOR, organization_id=ORG,
        invoice_id=inv.id, amount=Decimal("200.00"), currency="USD",
    )

    updated_inv = InvoiceUseCases(db_conn).get(inv.id, organization_id=ORG)
    assert updated_inv.status == "partially_paid"
    assert updated_inv.amount_paid == Decimal("200.00")
    assert updated_inv.amount_due == Decimal("300.00")


# ── MarkInvoicePastDue ────────────────────────────────────────────────────────

def test_mark_invoice_past_due(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, billing_profile_id=billing_profile,
    )
    InvoiceUseCases(db_conn).add_item(
        inv.id, actor_user_id=ACTOR, organization_id=ORG,
        description="Overdue item", quantity=Decimal("1"), unit_price=Decimal("99.00"),
    )
    InvoiceUseCases(db_conn).issue(inv.id, actor_user_id=ACTOR, organization_id=ORG)

    past_due = InvoiceUseCases(db_conn).mark_past_due(
        inv.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert past_due.status == "past_due"


# ── CreditNote ─────────────────────────────────────────────────────────────────

def test_create_and_apply_credit_note(db_conn, billing_profile):
    from app.packages.billing.application.use_cases import InvoiceUseCases, CreditNoteUseCases

    inv = InvoiceUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, billing_profile_id=billing_profile,
    )
    InvoiceUseCases(db_conn).add_item(
        inv.id, actor_user_id=ACTOR, organization_id=ORG,
        description="Credit me", quantity=Decimal("1"), unit_price=Decimal("75.00"),
    )
    InvoiceUseCases(db_conn).issue(inv.id, actor_user_id=ACTOR, organization_id=ORG)

    cn = CreditNoteUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG,
        invoice_id=inv.id, amount=Decimal("75.00"), reason="Full credit",
    )
    assert cn.status == "issued"
    assert cn.credit_note_number.startswith("CN-")

    applied = CreditNoteUseCases(db_conn).apply(
        cn.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert applied.status == "applied"

    updated_inv = InvoiceUseCases(db_conn).get(inv.id, organization_id=ORG)
    assert updated_inv.status == "credited"


# ── Ledger immutability ────────────────────────────────────────────────────────

def test_ledger_update_raises(db_conn):
    from app.packages.billing.application.use_cases import LedgerUseCases
    from app.packages.billing.domain.errors import LedgerImmutableError

    with pytest.raises(LedgerImmutableError):
        LedgerUseCases(db_conn).update_guard()


def test_ledger_delete_raises(db_conn):
    from app.packages.billing.application.use_cases import LedgerUseCases
    from app.packages.billing.domain.errors import LedgerImmutableError

    with pytest.raises(LedgerImmutableError):
        LedgerUseCases(db_conn).delete_guard()


# ── ProviderEvent idempotency ──────────────────────────────────────────────────

def test_provider_event_idempotent(db_conn):
    from app.packages.billing.application.use_cases import ProviderEventUseCases

    e1 = ProviderEventUseCases(db_conn).process(
        provider_code="academic_mock",
        provider_event_id="evt-l2-idempotent-001",
        event_type="payment.succeeded",
        payload='{"amount": 100}',
    )
    e2 = ProviderEventUseCases(db_conn).process(
        provider_code="academic_mock",
        provider_event_id="evt-l2-idempotent-001",
        event_type="payment.succeeded",
        payload='{"amount": 100}',
    )
    assert e1.id == e2.id


# ── Currency mismatch ──────────────────────────────────────────────────────────

def test_payment_attempt_currency_mismatch_raises(db_conn, draft_invoice):
    from app.packages.billing.application.use_cases import PaymentAttemptUseCases
    from app.packages.billing.domain.errors import CurrencyMismatchError

    with pytest.raises(CurrencyMismatchError):
        PaymentAttemptUseCases(db_conn).create(
            actor_user_id=ACTOR, organization_id=ORG,
            invoice_id=draft_invoice.id,
            provider_code="academic_mock",
            idempotency_key="l2-currency-mismatch-001",
            amount=Decimal("100.00"),
            currency="EUR",  # invoice is USD
        )
