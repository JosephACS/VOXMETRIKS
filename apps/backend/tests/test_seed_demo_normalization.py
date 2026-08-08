"""Demo personal seed — normalization and idempotency."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture()
def demo_seed_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_ACCOUNT_PASSWORD", "test-demo-secret-not-real")
    from app.core import schema_bootstrap

    schema_bootstrap._schema_ready = False
    db = tmp_path / "demo_seed.duckdb"
    conn = duckdb.connect(str(db))
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )

    ensure_user_tables(conn)
    ensure_personal_subscription_tables(conn)
    yield conn
    conn.close()
    schema_bootstrap._schema_ready = False


def _ids(seed_result: dict) -> dict[str, int]:
    return {a["username"]: int(a["user_id"]) for a in seed_result["accounts"]}


def test_listener_free_resets_after_premium_checkout(demo_seed_db):
    from app.packages.personal_subscriptions.application.seed_demo import seed_personal_demo
    from app.packages.personal_subscriptions.application.use_cases import (
        get_subscription,
        simulate_payment,
        start_checkout,
    )

    first = seed_personal_demo(demo_seed_db)
    assert first["ok"] is True
    free_id = _ids(first)["listener.free"]

    checkout = start_checkout(
        demo_seed_db, free_id, plan_code="premium_individual", billing_period="monthly"
    )
    simulate_payment(
        demo_seed_db, free_id, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    assert get_subscription(demo_seed_db, free_id)["plan_code"] == "premium_individual"

    for _ in range(3):
        assert seed_personal_demo(demo_seed_db)["ok"] is True

    free_sub = get_subscription(demo_seed_db, free_id)
    assert free_sub["plan_code"] == "personal_free"
    assert free_sub["is_free"] is True
    assert free_sub["status"] == "active"

    paid_invoices = int(
        demo_seed_db.execute(
            """
            SELECT COUNT(*) FROM personal_invoice
            WHERE user_id = ? AND status = 'paid'
            """,
            [free_id],
        ).fetchone()[0]
    )
    assert paid_invoices >= 1


def test_canonical_household_roster_includes_member3(demo_seed_db):
    from app.packages.personal_subscriptions.application.seed_demo import (
        DEMO_ACCOUNTS,
        seed_personal_demo,
    )
    from app.packages.personal_subscriptions.application.use_cases import get_household

    seed_personal_demo(demo_seed_db)
    seed_personal_demo(demo_seed_db)
    roster = {u for u, _ in DEMO_ACCOUNTS}
    assert "household.member3" in roster

    owner_id = int(
        demo_seed_db.execute(
            "SELECT id FROM app_user WHERE username = 'household.owner'"
        ).fetchone()[0]
    )
    hh = get_household(demo_seed_db, owner_id)
    assert hh["plan_code"] == "premium_family"
    assert hh["my_role"] == "owner"
    assert hh["max_members"] == 6
    active = {
        m.get("username") or m.get("login_hint")
        for m in hh["members"]
        if m.get("status") == "active"
    }
    assert "household.member" in active
    assert "household.member2" in active
    assert "household.member3" in active


def test_pending_invitation_unique_and_idempotent(demo_seed_db):
    from app.core.time_util import utc_now
    from app.packages.personal_subscriptions.application.seed_demo import seed_personal_demo

    seed_personal_demo(demo_seed_db)
    owner_id = int(
        demo_seed_db.execute(
            "SELECT id FROM app_user WHERE username = 'household.owner'"
        ).fetchone()[0]
    )
    email_n = "household.pending@demo.voxmetriks.local"

    def pending_rows():
        return demo_seed_db.execute(
            """
            SELECT hi.id, hi.expires_at, hi.status
            FROM household_invitation hi
            JOIN household h ON h.id = hi.household_id
            WHERE h.owner_user_id = ?
              AND hi.email_normalized = ?
            ORDER BY hi.id ASC
            """,
            [owner_id, email_n],
        ).fetchall()

    def valid_pending():
        now = utc_now()
        return [
            (int(i), exp)
            for i, exp, status in pending_rows()
            if status == "pending" and exp is not None and exp > now
        ]

    assert len(valid_pending()) == 1
    assert valid_pending()[0][1] > utc_now()

    seed_personal_demo(demo_seed_db)
    seed_personal_demo(demo_seed_db)
    after_reseed = valid_pending()
    assert len(after_reseed) == 1
    assert after_reseed[0][1] > utc_now()

    # Inject two additional valid pending invites (duplicates).
    hh_id = int(
        demo_seed_db.execute(
            "SELECT id FROM household WHERE owner_user_id = ? AND status = 'active'",
            [owner_id],
        ).fetchone()[0]
    )
    now = utc_now()
    from datetime import timedelta

    far = now + timedelta(days=7)
    for _ in range(2):
        inv_id = int(
            demo_seed_db.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM household_invitation"
            ).fetchone()[0]
        )
        demo_seed_db.execute(
            """
            INSERT INTO household_invitation (
                id, household_id, email_normalized, invited_by_user_id, token_hash,
                status, expires_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            [
                inv_id,
                hh_id,
                email_n,
                owner_id,
                f"dup-hash-{inv_id}",
                far,
                now,
                now,
            ],
        )

    assert len(valid_pending()) >= 3
    kept_before = valid_pending()[0][0]  # oldest id

    seed_personal_demo(demo_seed_db)
    final_valid = valid_pending()
    assert len(final_valid) == 1
    assert final_valid[0][0] == kept_before
    assert final_valid[0][1] > utc_now()

    canceled = [
        int(i)
        for i, exp, status in pending_rows()
        if status == "canceled"
    ]
    assert len(canceled) >= 2
    expired_dupes = [
        int(i)
        for i, exp, status in pending_rows()
        if status == "expired" and exp is not None and exp > utc_now()
    ]
    assert expired_dupes == []


def test_listener_premium_single_active_subscription(demo_seed_db):
    from app.packages.personal_subscriptions.application.seed_demo import seed_personal_demo
    from app.packages.personal_subscriptions.application.use_cases import get_subscription

    seed_personal_demo(demo_seed_db)
    seed_personal_demo(demo_seed_db)
    prem_id = int(
        demo_seed_db.execute(
            "SELECT id FROM app_user WHERE username = 'listener.premium'"
        ).fetchone()[0]
    )
    prem = get_subscription(demo_seed_db, prem_id)
    assert prem["plan_code"] == "premium_individual"
    assert prem["status"] == "active"
    count = int(
        demo_seed_db.execute(
            """
            SELECT COUNT(*) FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            WHERE s.user_id = ? AND p.code = 'premium_individual' AND s.status = 'active'
            """,
            [prem_id],
        ).fetchone()[0]
    )
    assert count == 1


def test_normalize_listener_free_rolls_back_on_failure(demo_seed_db, monkeypatch):
    from app.packages.personal_subscriptions.application import seed_demo as seed_mod
    from app.packages.personal_subscriptions.application.seed_demo import (
        seed_personal_demo,
        _normalize_listener_free,
    )
    from app.packages.personal_subscriptions.application.use_cases import (
        get_subscription,
        simulate_payment,
        start_checkout,
    )

    seed_personal_demo(demo_seed_db)
    free_id = int(
        demo_seed_db.execute(
            "SELECT id FROM app_user WHERE username = 'listener.free'"
        ).fetchone()[0]
    )
    checkout = start_checkout(
        demo_seed_db, free_id, plan_code="premium_individual", billing_period="monthly"
    )
    simulate_payment(
        demo_seed_db, free_id, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    assert get_subscription(demo_seed_db, free_id)["plan_code"] == "premium_individual"

    real_cancel = seed_mod.cancel_subscription

    def _cancel_then_fail(conn, user_id, *, at_period_end=True):
        real_cancel(conn, user_id, at_period_end=at_period_end)
        raise RuntimeError("injected normalize failure")

    monkeypatch.setattr(seed_mod, "cancel_subscription", _cancel_then_fail)
    with pytest.raises(RuntimeError, match="injected normalize failure"):
        _normalize_listener_free(demo_seed_db, free_id)

    assert get_subscription(demo_seed_db, free_id)["plan_code"] == "premium_individual"
