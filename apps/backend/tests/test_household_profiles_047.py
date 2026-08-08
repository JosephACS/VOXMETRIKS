# -*- coding: utf-8 -*-
"""Spec 047 — household profiles list + prepare-switch security."""

from __future__ import annotations

import duckdb
import pytest

from app.packages.personal_subscriptions.domain.errors import PersonalForbiddenError


@pytest.fixture()
def personal_db(tmp_path):
    from app.core import schema_bootstrap
    from app.core.time_util import utc_now
    from app.packages.engagement.services.app_storage import ensure_app_tables
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables

    schema_bootstrap._schema_ready = False
    db = tmp_path / "household_profiles.duckdb"
    c = duckdb.connect(str(db))
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
            ("u_owner", "u_owner@test.local"),
            ("u_member", "u_member@test.local"),
            ("u_third", "u_third@test.local"),
            ("u_extra", "u_extra@test.local"),
            ("u_f2", "u_f2@test.local"),
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


def _activate_duo(conn, owner: int, member: int, member_email: str) -> None:
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        ensure_free_subscription,
        invite_member,
        simulate_payment,
        start_checkout,
    )

    for uid in (owner, member):
        ensure_free_subscription(conn, uid)
    checkout = start_checkout(conn, owner, plan_code="premium_duo", billing_period="monthly")
    simulate_payment(conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded")
    inv = invite_member(conn, owner, member_email)
    accept_invitation(conn, member, inv["token"])


def test_list_profiles_safe_no_emails_or_login_hints(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import list_household_profiles

    owner = uids["u_owner"]
    member = uids["u_member"]
    _activate_duo(personal_conn, owner, member, "u_member@test.local")

    payload = list_household_profiles(personal_conn, owner)
    assert payload["show_selector"] is True
    assert len(payload["profiles"]) == 2
    blob = str(payload)
    assert "@test.local" not in blob
    assert "login_hint" not in blob
    assert "password" not in blob.lower()
    assert "token" not in blob.lower()
    for p in payload["profiles"]:
        assert "email" not in p
        assert "username" not in p
        assert "login_hint" not in p
        assert p["display_name"]
        assert p["profile_key"].startswith("p")


def test_list_profiles_no_household(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
        list_household_profiles,
    )

    uid = uids["u_free"]
    ensure_free_subscription(personal_conn, uid)
    payload = list_household_profiles(personal_conn, uid)
    assert payload["household"] is None
    assert payload["profiles"] == []
    assert payload["show_selector"] is False


def test_prepare_switch_external_target_forbidden(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import prepare_profile_switch

    owner = uids["u_owner"]
    member = uids["u_member"]
    outsider = uids["u_third"]
    _activate_duo(personal_conn, owner, member, "u_member@test.local")

    with pytest.raises(PersonalForbiddenError):
        prepare_profile_switch(personal_conn, owner, outsider)


def test_prepare_switch_self_rejected(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import prepare_profile_switch

    owner = uids["u_owner"]
    member = uids["u_member"]
    _activate_duo(personal_conn, owner, member, "u_member@test.local")

    with pytest.raises(PersonalForbiddenError):
        prepare_profile_switch(personal_conn, owner, owner)


def test_prepare_switch_authorized_returns_hint_only(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import prepare_profile_switch

    owner = uids["u_owner"]
    member = uids["u_member"]
    _activate_duo(personal_conn, owner, member, "u_member@test.local")

    out = prepare_profile_switch(personal_conn, owner, member)
    assert set(out.keys()) == {"login_hint", "display_name"}
    assert out["login_hint"]
    assert "token" not in out
    assert "session" not in out
    assert "password" not in out


def test_inactive_plan_limits_profiles_to_self(personal_conn, uids):
    from app.packages.personal_subscriptions.application.use_cases import list_household_profiles

    owner = uids["u_extra"]
    member = uids["u_f2"]
    _activate_duo(personal_conn, owner, member, "u_f2@test.local")

    # Force owner paid subscription inactive while household membership rows remain.
    personal_conn.execute(
        """
        UPDATE personal_subscription
        SET status = 'canceled'
        WHERE user_id = ?
          AND plan_id IN (SELECT id FROM personal_plan WHERE is_free = FALSE)
        """,
        [owner],
    )

    payload = list_household_profiles(personal_conn, owner)
    assert payload["plan_active"] is False
    assert len(payload["profiles"]) == 1
    assert payload["profiles"][0]["is_me"] is True
    assert payload["show_selector"] is False
