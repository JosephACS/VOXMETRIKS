"""Spec 029 — Personal music subscriptions golden path + security."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture()
def personal_db(tmp_path):
    from app.core import schema_bootstrap

    schema_bootstrap._schema_ready = False
    db = tmp_path / "personal.duckdb"
    c = duckdb.connect(str(db))
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.engagement.services.app_storage import ensure_app_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now

    ensure_user_tables(c)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR,
            nombre_track VARCHAR NOT NULL, id_artista INTEGER, id_album INTEGER,
            id_genero INTEGER, explicit BOOLEAN DEFAULT FALSE,
            duration_ms INTEGER, popularity INTEGER
        )
        """
    )
    if int(c.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]) == 0:
        for tid in range(1, 60):
            c.execute(
                "INSERT INTO dim_track (id_track, nombre_track, popularity) VALUES (?, ?, ?)",
                [tid, f"Track {tid}", 50],
            )
    ensure_app_tables(c)
    ensure_platform_ops_tables(c)
    ensure_personal_subscription_tables(c)
    now = utc_now()
    base = int(c.execute("SELECT COALESCE(MAX(id), 0) FROM app_user").fetchone()[0])
    users: dict[str, int] = {}
    for i, (uname, email) in enumerate(
        [
            ("u_free", "u_free@test.local"),
            ("u_prem", "u_prem@test.local"),
            ("u_owner", "u_owner@test.local"),
            ("u_member", "u_member@test.local"),
            ("u_third", "u_third@test.local"),
            ("u_extra", "u_extra@test.local"),
            ("u_f2", "u_f2@test.local"),
            ("u_f3", "u_f3@test.local"),
            ("u_f4", "u_f4@test.local"),
            ("u_f5", "u_f5@test.local"),
            ("u_f6", "u_f6@test.local"),
            ("u_f7", "u_f7@test.local"),
        ],
        start=1,
    ):
        uid = base + i
        c.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre,
                 created_at, preferences_json, email_verified, auth_provider)
            VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, '{}', TRUE, 'local')
            """,
            [uid, uname, email, hash_password("pass"), now],
        )
        users[uname] = uid
    yield c, users
    c.close()


@pytest.fixture()
def personal_conn(personal_db):
    return personal_db[0]


@pytest.fixture()
def uids(personal_db):
    return personal_db[1]


def test_catalog_and_free_assignment(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
        list_personal_plans,
    )

    plans = list_personal_plans(personal_conn)
    codes = {p["code"] for p in plans}
    assert codes == {
        "personal_free",
        "premium_individual",
        "premium_duo",
        "premium_family",
    }
    free = next(p for p in plans if p["code"] == "personal_free")
    assert free["prices"][0]["amount"] == 0.0
    individual = next(p for p in plans if p["code"] == "premium_individual")
    amounts = {pr["billing_period"]: pr["amount"] for pr in individual["prices"]}
    assert amounts["monthly"] == 4.99
    assert amounts["annual"] == 49.90

    uid = uids["u_free"]
    sub = ensure_free_subscription(personal_conn, uid)
    assert sub["plan_code"] == "personal_free"
    assert sub["owner_type"] == "user"
    sub2 = ensure_free_subscription(personal_conn, uid)
    assert sub2["id"] == sub["id"]


def test_free_playlist_limit_and_upgrade(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
        simulate_payment,
        start_checkout,
    )
    from app.packages.engagement.services.playlist_service import create_playlist
    from app.packages.personal_subscriptions.domain.errors import EntitlementLimitError

    uid = uids["u_free"]
    ensure_free_subscription(personal_conn, uid)
    for i in range(3):
        create_playlist(personal_conn, uid, f"P{i}")
    with pytest.raises(EntitlementLimitError):
        from app.packages.personal_subscriptions.application.entitlements import (
            assert_can_create_playlist,
        )

        assert_can_create_playlist(personal_conn, uid)

    checkout = start_checkout(
        personal_conn, uid, plan_code="premium_individual", billing_period="monthly"
    )
    simulate_payment(
        personal_conn, uid, attempt_id=checkout["attempt_id"], scenario="declined"
    )
    checkout2 = start_checkout(
        personal_conn, uid, plan_code="premium_individual", billing_period="monthly"
    )
    ok = simulate_payment(
        personal_conn, uid, attempt_id=checkout2["attempt_id"], scenario="succeeded"
    )
    assert ok["status"] == "succeeded"
    from app.packages.personal_subscriptions.application.use_cases import get_subscription

    sub = get_subscription(personal_conn, uid)
    assert sub["plan_code"] == "premium_individual"
    assert sub["status"] == "active"
    create_playlist(personal_conn, uid, "P4")


def test_duo_capacity_and_isolation(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        ensure_free_subscription,
        get_household,
        invite_member,
        simulate_payment,
        start_checkout,
    )
    from app.packages.personal_subscriptions.domain.errors import HouseholdCapacityError

    owner = uids["u_owner"]
    member = uids["u_member"]
    for uid in (owner, member, uids["u_third"]):
        ensure_free_subscription(personal_conn, uid)
    checkout = start_checkout(
        personal_conn, owner, plan_code="premium_duo", billing_period="monthly"
    )
    simulate_payment(
        personal_conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    inv = invite_member(personal_conn, owner, "u_member@test.local")
    accept_invitation(personal_conn, member, inv["token"])
    hh = get_household(personal_conn, owner)
    assert hh["seats_used"] == 2
    assert hh["seats_available"] == 0
    with pytest.raises(HouseholdCapacityError):
        invite_member(personal_conn, owner, "u_third@test.local")

    from app.packages.personal_subscriptions.domain.errors import PersonalForbiddenError

    with pytest.raises(PersonalForbiddenError):
        invite_member(personal_conn, member, "u_third@test.local")


def test_family_max_six(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        ensure_free_subscription,
        invite_member,
        simulate_payment,
        start_checkout,
    )
    from app.packages.personal_subscriptions.domain.errors import HouseholdCapacityError

    owner = uids["u_extra"]
    ensure_free_subscription(personal_conn, owner)
    checkout = start_checkout(
        personal_conn, owner, plan_code="premium_family", billing_period="annual"
    )
    simulate_payment(
        personal_conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    member_keys = ["u_f2", "u_f3", "u_f4", "u_f5", "u_f6"]
    emails = [
        "u_f2@test.local",
        "u_f3@test.local",
        "u_f4@test.local",
        "u_f5@test.local",
        "u_f6@test.local",
    ]
    for key, email in zip(member_keys, emails):
        uid = uids[key]
        ensure_free_subscription(personal_conn, uid)
        inv = invite_member(personal_conn, owner, email)
        accept_invitation(personal_conn, uid, inv["token"])
    ensure_free_subscription(personal_conn, uids["u_f7"])
    with pytest.raises(HouseholdCapacityError):
        invite_member(personal_conn, owner, "u_f7@test.local")


def test_cancel_refund_metrics_and_idor(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        cancel_subscription,
        ensure_free_subscription,
        personal_metrics,
        refund_latest_paid,
        simulate_payment,
        start_checkout,
    )
    from app.packages.personal_subscriptions.domain.errors import PersonalNotFoundError

    prem = uids["u_prem"]
    free = uids["u_free"]
    ensure_free_subscription(personal_conn, prem)
    checkout = start_checkout(
        personal_conn, prem, plan_code="premium_individual", billing_period="monthly"
    )
    simulate_payment(
        personal_conn, prem, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    refund_latest_paid(personal_conn, prem)
    sub_after = ensure_free_subscription(personal_conn, prem)
    assert sub_after["is_free"] or sub_after["plan_code"] == "personal_free"

    ensure_free_subscription(personal_conn, free)
    checkout = start_checkout(
        personal_conn, free, plan_code="premium_individual", billing_period="monthly"
    )
    simulate_payment(
        personal_conn, free, attempt_id=checkout["attempt_id"], scenario="succeeded"
    )
    cancel_subscription(personal_conn, free, at_period_end=False)
    metrics = personal_metrics(personal_conn)
    assert metrics["segment"] == "B2C"
    assert metrics["currency"] == "USD"

    with pytest.raises(PersonalNotFoundError):
        simulate_payment(
            personal_conn, prem, attempt_id=checkout["attempt_id"], scenario="succeeded"
        )


def test_b2b_untouched_by_personal_schema(personal_conn):
    """Personal catalog must not create B2B plan codes."""
    rows = personal_conn.execute(
        "SELECT code FROM personal_plan ORDER BY code"
    ).fetchall()
    codes = [r[0] for r in rows]
    assert "starter" not in codes
    assert "enterprise" not in codes


def test_list_personal_plans_owner_type(personal_conn):
    from app.packages.personal_subscriptions.application.use_cases import list_personal_plans

    items = list_personal_plans(personal_conn)
    assert len(items) == 4
    assert all(
        p["code"].startswith("personal_") or p["code"].startswith("premium_")
        for p in items
    )


def test_resend_invitation_rolls_back_when_insert_fails(personal_conn, uids, monkeypatch):
    from app.packages.personal_subscriptions.application import use_cases as uc
    from app.packages.personal_subscriptions.application.use_cases import (
        invite_member,
        resend_invitation,
        start_checkout,
        simulate_payment,
    )

    conn = personal_conn
    owner = uids["u_owner"]
    checkout = start_checkout(
        conn, owner, plan_code="premium_duo", billing_period="monthly"
    )
    simulate_payment(conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded")
    inv = invite_member(conn, owner, "newinvite@test.local")
    inv_id = int(inv["invitation_id"])
    before = conn.execute(
        "SELECT email_normalized, token_hash, status FROM household_invitation WHERE id = ?",
        [inv_id],
    ).fetchone()

    monkeypatch.setattr(
        uc,
        "_hash_token",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("injected insert failure")),
    )
    with pytest.raises(RuntimeError, match="injected insert failure"):
        resend_invitation(conn, owner, inv_id)

    after = conn.execute(
        "SELECT email_normalized, token_hash, status FROM household_invitation WHERE id = ?",
        [inv_id],
    ).fetchone()
    assert after is not None
    assert after[0] == before[0]
    assert after[1] == before[1]
    assert after[2] == "pending"


def test_leave_household_rolls_back_on_event_failure(personal_conn, uids, monkeypatch):
    from app.packages.personal_subscriptions.application import use_cases as uc
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        invite_member,
        leave_household,
        start_checkout,
        simulate_payment,
    )

    conn = personal_conn
    owner = uids["u_prem"]
    member = uids["u_third"]
    checkout = start_checkout(
        conn, owner, plan_code="premium_duo", billing_period="monthly"
    )
    simulate_payment(conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded")
    inv = invite_member(conn, owner, "u_third@test.local")
    accept_invitation(conn, member, inv["token"])

    monkeypatch.setattr(
        uc,
        "_emit_event",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected event failure")),
    )
    with pytest.raises(RuntimeError, match="injected event failure"):
        leave_household(conn, member)

    status = conn.execute(
        """
        SELECT hm.status FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND h.status = 'active'
        ORDER BY hm.id DESC LIMIT 1
        """,
        [member],
    ).fetchone()
    assert status is not None
    assert status[0] == "active"
