"""Refund idempotency — unique key, replay, concurrency, available balance."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import duckdb
import pytest


@pytest.fixture()
def refund_db(tmp_path):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path / "refund_idem.duckdb"
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
    conn.execute("""
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at)
        VALUES (500, 'Refund Idem Org', 'Refund Idem LLC', 'refund-idem-org', 'label', 'US',
                'UTC', 'USD', 'active', 1, ?, ?)
    """, [now, now])

    yield conn, str(db_path)
    conn.close()
    schema_bootstrap._schema_ready = previous


ACTOR = 1
ORG = 500


def _seed_payment(conn, *, amount: str = "100.00", payment_id: int = 1) -> int:
    from app.core.time_util import utc_now

    now = utc_now()
    attempt_id = payment_id + 1000
    conn.execute("""
        INSERT INTO app_payment_attempt
            (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
             idempotency_key, amount, currency, status, provider_attempt_id,
             failure_reason, created_at, updated_at)
        VALUES (?, ?, 1, NULL, 'academic_mock', ?, ?, 'USD', 'succeeded', NULL, NULL, ?, ?)
    """, [attempt_id, ORG, f"seed-attempt-{attempt_id}", amount, now, now])
    conn.execute("""
        INSERT INTO app_payment
            (id, organization_id, payment_attempt_id, provider_code, amount, currency,
             status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
        VALUES (?, ?, ?, 'academic_mock', ?, 'USD', 'settled', ?, NULL, NULL, ?, ?)
    """, [payment_id, ORG, attempt_id, amount, f"pay-{payment_id}", now, now])
    return payment_id


def test_refund_idempotency_key_unique_constraint(refund_db):
    conn, _ = refund_db
    from app.core.time_util import utc_now

    now = utc_now()
    _seed_payment(conn, payment_id=10)
    conn.execute("""
        INSERT INTO app_refund
            (id, organization_id, payment_id, amount, currency, reason, status,
             processed_at, created_at, updated_at, idempotency_key)
        VALUES (1, ?, 10, 10.0, 'USD', 'a', 'processed', ?, ?, ?, 'rk-unique-1')
    """, [ORG, now, now, now])
    with pytest.raises(Exception):
        conn.execute("""
            INSERT INTO app_refund
                (id, organization_id, payment_id, amount, currency, reason, status,
                 processed_at, created_at, updated_at, idempotency_key)
            VALUES (2, ?, 10, 5.0, 'USD', 'b', 'processed', ?, ?, ?, 'rk-unique-1')
        """, [ORG, now, now, now])


def test_first_create_and_replay_same_key(refund_db):
    from app.packages.billing.application.use_cases import RefundUseCases

    conn, _ = refund_db
    pay_id = _seed_payment(conn, amount="100.00", payment_id=20)
    uc = RefundUseCases(conn)

    first = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("40.00"),
        reason="partial",
        idempotency_key="replay-key-1",
    )
    assert first.created is True
    assert first.refund.id > 0

    second = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("40.00"),
        reason="partial",
        idempotency_key="replay-key-1",
    )
    assert second.created is False
    assert second.refund.id == first.refund.id

    refund_count = int(
        conn.execute("SELECT COUNT(*) FROM app_refund WHERE payment_id = ?", [pay_id]).fetchone()[0]
    )
    ledger_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_billing_ledger_entry "
            "WHERE entry_type = 'refund_issued' AND reference_id = ?",
            [first.refund.id],
        ).fetchone()[0]
    )
    assert refund_count == 1
    assert ledger_count == 1

    pay_status = conn.execute(
        "SELECT status FROM app_payment WHERE id = ?", [pay_id]
    ).fetchone()[0]
    assert pay_status == "partially_refunded"


def test_same_key_different_payload_rejected(refund_db):
    from app.packages.billing.application.use_cases import RefundUseCases
    from app.packages.billing.domain.errors import IdempotencyConflictError

    conn, _ = refund_db
    pay_id = _seed_payment(conn, payment_id=30)
    uc = RefundUseCases(conn)
    uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("10.00"),
        reason="a",
        idempotency_key="conflict-key",
    )
    with pytest.raises(IdempotencyConflictError):
        uc.create(
            actor_user_id=ACTOR,
            organization_id=ORG,
            payment_id=pay_id,
            amount=Decimal("20.00"),
            reason="a",
            idempotency_key="conflict-key",
        )


def test_new_key_allows_second_refund_within_balance(refund_db):
    from app.packages.billing.application.use_cases import RefundUseCases

    conn, _ = refund_db
    pay_id = _seed_payment(conn, amount="100.00", payment_id=40)
    uc = RefundUseCases(conn)
    r1 = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("30.00"),
        idempotency_key="key-a",
    )
    r2 = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("25.00"),
        idempotency_key="key-b",
    )
    assert r1.created and r2.created
    assert r1.refund.id != r2.refund.id
    count = int(
        conn.execute("SELECT COUNT(*) FROM app_refund WHERE payment_id = ?", [pay_id]).fetchone()[0]
    )
    assert count == 2
    ledger = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_billing_ledger_entry "
            "WHERE entry_type = 'refund_issued' AND organization_id = ?",
            [ORG],
        ).fetchone()[0]
    )
    assert ledger == 2


def test_amount_over_available_blocked(refund_db):
    from app.packages.billing.application.use_cases import RefundUseCases
    from app.packages.billing.domain.errors import InsufficientFundsError

    conn, _ = refund_db
    pay_id = _seed_payment(conn, amount="50.00", payment_id=50)
    uc = RefundUseCases(conn)
    uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_id,
        amount=Decimal("40.00"),
        idempotency_key="over-1",
    )
    with pytest.raises(InsufficientFundsError):
        uc.create(
            actor_user_id=ACTOR,
            organization_id=ORG,
            payment_id=pay_id,
            amount=Decimal("20.00"),
            idempotency_key="over-2",
        )


def test_five_concurrent_same_key_one_row(refund_db):
    """Five concurrent creates with the same key yield one refund and one ledger entry."""
    conn, db_path = refund_db
    pay_id = _seed_payment(conn, amount="100.00", payment_id=60)
    # Ensure writer has flushed before worker connections attach.
    conn.execute("CHECKPOINT")

    def worker(_idx: int):
        c = duckdb.connect(db_path)
        try:
            from app.packages.billing.application.use_cases import RefundUseCases

            result = RefundUseCases(c).create(
                actor_user_id=ACTOR,
                organization_id=ORG,
                payment_id=pay_id,
                amount=Decimal("15.00"),
                reason="concurrent",
                idempotency_key="concurrent-key-5",
            )
            return result.refund.id, result.created
        finally:
            c.close()

    outcomes = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(worker, i) for i in range(5)]
        for fut in as_completed(futures):
            outcomes.append(fut.result())

    ids = {oid for oid, _ in outcomes}
    assert len(ids) == 1
    created_flags = [c for _, c in outcomes]
    assert sum(1 for c in created_flags if c) <= 1

    verify = duckdb.connect(db_path)
    try:
        refund_n = int(
            verify.execute(
                "SELECT COUNT(*) FROM app_refund WHERE idempotency_key = ?",
                ["concurrent-key-5"],
            ).fetchone()[0]
        )
        ledger_n = int(
            verify.execute(
                "SELECT COUNT(*) FROM app_billing_ledger_entry "
                "WHERE entry_type = 'refund_issued' AND reference_id = ?",
                [next(iter(ids))],
            ).fetchone()[0]
        )
        pay_status = verify.execute(
            "SELECT status FROM app_payment WHERE id = ?", [pay_id]
        ).fetchone()[0]
    finally:
        verify.close()

    assert refund_n == 1
    assert ledger_n == 1
    assert pay_status == "partially_refunded"


def test_invoice_unchanged_by_refund_replay(refund_db):
    """Refunds do not mutate invoice totals; replay must not invent extra effects."""
    from app.packages.billing.application.use_cases import (
        BillingProfileUseCases,
        InvoiceUseCases,
        PaymentUseCases,
        RefundUseCases,
    )

    conn, _ = refund_db
    profile = BillingProfileUseCases(conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        default_currency="USD",
        legal_name="Refund Idem LLC",
    )
    inv = InvoiceUseCases(conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        billing_profile_id=profile.id,
    )
    InvoiceUseCases(conn).add_item(
        inv.id,
        actor_user_id=ACTOR,
        organization_id=ORG,
        description="Item",
        quantity=Decimal("1"),
        unit_price=Decimal("80.00"),
    )
    InvoiceUseCases(conn).issue(inv.id, actor_user_id=ACTOR, organization_id=ORG)
    payment = PaymentUseCases(conn).record_manual(
        actor_user_id=ACTOR,
        organization_id=ORG,
        invoice_id=inv.id,
        amount=Decimal("80.00"),
        currency="USD",
    )
    before = InvoiceUseCases(conn).get(inv.id, organization_id=ORG)
    uc = RefundUseCases(conn)
    r1 = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=payment.id,
        amount=Decimal("10.00"),
        idempotency_key="inv-refund-1",
    )
    r2 = uc.create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=payment.id,
        amount=Decimal("10.00"),
        idempotency_key="inv-refund-1",
    )
    after = InvoiceUseCases(conn).get(inv.id, organization_id=ORG)
    assert r1.refund.id == r2.refund.id
    assert after.amount_paid == before.amount_paid
    assert after.amount_due == before.amount_due
    assert after.status == before.status

def test_same_key_isolated_across_organizations(refund_db):
    """Same idempotency_key in two orgs must not cross or leak."""
    from app.core.time_util import utc_now
    from app.packages.billing.application.use_cases import RefundUseCases

    conn, _ = refund_db
    now = utc_now()
    conn.execute("""
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at)
        VALUES (501, 'Other Org', 'Other LLC', 'refund-idem-org-2', 'label', 'US',
                'UTC', 'USD', 'active', 1, ?, ?)
    """, [now, now])
    pay_a = _seed_payment(conn, amount="100.00", payment_id=70)
    # Payment for org 501
    attempt_id = 1701
    conn.execute("""
        INSERT INTO app_payment_attempt
            (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
             idempotency_key, amount, currency, status, provider_attempt_id,
             failure_reason, created_at, updated_at)
        VALUES (?, 501, 1, NULL, 'academic_mock', ?, '100.00', 'USD', 'succeeded',
                NULL, NULL, ?, ?)
    """, [attempt_id, f"seed-attempt-{attempt_id}", now, now])
    conn.execute("""
        INSERT INTO app_payment
            (id, organization_id, payment_attempt_id, provider_code, amount, currency,
             status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
        VALUES (71, 501, ?, 'academic_mock', '100.00', 'USD', 'settled', 'pay-71',
                NULL, NULL, ?, ?)
    """, [attempt_id, now, now])

    shared_key = "shared-org-key"
    a = RefundUseCases(conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_a,
        amount=Decimal("10.00"),
        idempotency_key=shared_key,
    )
    b = RefundUseCases(conn).create(
        actor_user_id=ACTOR,
        organization_id=501,
        payment_id=71,
        amount=Decimal("12.00"),
        idempotency_key=shared_key,
    )
    assert a.created and b.created
    assert a.refund.id != b.refund.id
    assert a.refund.organization_id == ORG
    assert b.refund.organization_id == 501
    assert a.refund.amount == Decimal("10.00")
    assert b.refund.amount == Decimal("12.00")

    # Org A replay must never see org B's refund.
    replay = RefundUseCases(conn).create(
        actor_user_id=ACTOR,
        organization_id=ORG,
        payment_id=pay_a,
        amount=Decimal("10.00"),
        idempotency_key=shared_key,
    )
    assert replay.created is False
    assert replay.refund.id == a.refund.id
    assert replay.refund.organization_id == ORG


def test_pending_refund_is_not_successful_replay(refund_db):
    from app.core.time_util import utc_now
    from app.packages.billing.application.use_cases import RefundUseCases
    from app.packages.billing.domain.errors import ConflictError

    conn, _ = refund_db
    pay_id = _seed_payment(conn, payment_id=80)
    now = utc_now()
    conn.execute("""
        INSERT INTO app_refund
            (id, organization_id, payment_id, amount, currency, reason, status,
             processed_at, created_at, updated_at, idempotency_key)
        VALUES (801, ?, ?, 5.0, 'USD', 'x', 'pending', NULL, ?, ?, 'pending-key')
    """, [ORG, pay_id, now, now])
    with pytest.raises(ConflictError):
        RefundUseCases(conn).create(
            actor_user_id=ACTOR,
            organization_id=ORG,
            payment_id=pay_id,
            amount=Decimal("5.00"),
            reason="x",
            idempotency_key="pending-key",
        )


def test_concurrent_different_keys_cannot_over_refund(refund_db):
    """Two distinct keys racing for remaining balance: at most one full over-claim wins."""
    conn, db_path = refund_db
    pay_id = _seed_payment(conn, amount="50.00", payment_id=90)
    conn.execute("CHECKPOINT")

    def worker(key: str):
        c = duckdb.connect(db_path)
        try:
            from app.packages.billing.application.use_cases import RefundUseCases
            from app.packages.billing.domain.errors import InsufficientFundsError

            try:
                result = RefundUseCases(c).create(
                    actor_user_id=ACTOR,
                    organization_id=ORG,
                    payment_id=pay_id,
                    amount=Decimal("40.00"),
                    idempotency_key=key,
                )
                return ("ok", result.refund.id, result.created)
            except InsufficientFundsError:
                return ("insufficient", None, False)
        finally:
            c.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, "race-a"), pool.submit(worker, "race-b")]
        outcomes = [f.result() for f in as_completed(futures)]

    oks = [o for o in outcomes if o[0] == "ok"]
    fails = [o for o in outcomes if o[0] == "insufficient"]
    assert len(oks) == 1
    assert len(fails) == 1

    verify = duckdb.connect(db_path)
    try:
        refund_n = int(
            verify.execute(
                "SELECT COUNT(*) FROM app_refund WHERE payment_id = ? AND status = 'processed'",
                [pay_id],
            ).fetchone()[0]
        )
        total = Decimal(
            str(
                verify.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM app_refund "
                    "WHERE payment_id = ? AND status = 'processed'",
                    [pay_id],
                ).fetchone()[0]
            )
        )
        ledger_n = int(
            verify.execute(
                "SELECT COUNT(*) FROM app_billing_ledger_entry "
                "WHERE entry_type = 'refund_issued' AND organization_id = ?",
                [ORG],
            ).fetchone()[0]
        )
    finally:
        verify.close()
    assert refund_n == 1
    assert total == Decimal("40.00")
    assert ledger_n == 1


def test_injected_failure_rolls_back_refund_completely(refund_db, monkeypatch):
    from app.packages.billing.application import use_cases as uc_mod
    from app.packages.billing.application.use_cases import RefundUseCases

    conn, _ = refund_db
    pay_id = _seed_payment(conn, amount="100.00", payment_id=100)
    before_status = conn.execute(
        "SELECT status FROM app_payment WHERE id = ?", [pay_id]
    ).fetchone()[0]

    def boom(*_a, **_k):
        raise RuntimeError("injected ledger failure")

    monkeypatch.setattr(uc_mod, "_append_ledger", boom)
    with pytest.raises(RuntimeError, match="injected ledger failure"):
        RefundUseCases(conn).create(
            actor_user_id=ACTOR,
            organization_id=ORG,
            payment_id=pay_id,
            amount=Decimal("15.00"),
            idempotency_key="rollback-key",
        )

    assert (
        int(
            conn.execute(
                "SELECT COUNT(*) FROM app_refund WHERE payment_id = ?", [pay_id]
            ).fetchone()[0]
        )
        == 0
    )
    assert (
        int(
            conn.execute(
                "SELECT COUNT(*) FROM app_billing_ledger_entry "
                "WHERE entry_type = 'refund_issued' AND organization_id = ?",
                [ORG],
            ).fetchone()[0]
        )
        == 0
    )
    assert (
        conn.execute("SELECT status FROM app_payment WHERE id = ?", [pay_id]).fetchone()[0]
        == before_status
    )

