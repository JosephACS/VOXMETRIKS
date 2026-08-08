"""Opt-in demo seed for personal subscriptions — Spec 029.

Idempotent. Marked demo. Does NOT use pytest user names.
Passwords come from env DEMO_PASSWORD (never committed).
"""

from __future__ import annotations

import os
from typing import Any, Dict

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.identity.services.password_security import hash_password
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.personal_subscriptions.application.use_cases import (
    accept_invitation,
    cancel_subscription,
    ensure_free_subscription,
    get_household,
    invite_member,
    simulate_payment,
    start_checkout,
)
from app.packages.personal_subscriptions.domain.errors import (
    PersonalNotFoundError,
)
from app.packages.personal_subscriptions.infrastructure.schema import (
    ensure_personal_subscription_tables,
)

DEMO_ACCOUNTS = (
    ("listener.free", "listener.free@demo.voxmetriks.local"),
    ("listener.premium", "listener.premium@demo.voxmetriks.local"),
    ("household.owner", "household.owner@demo.voxmetriks.local"),
    ("household.member", "household.member@demo.voxmetriks.local"),
    ("household.member2", "household.member2@demo.voxmetriks.local"),
    ("household.member3", "household.member3@demo.voxmetriks.local"),
    ("listener.pastdue", "listener.pastdue@demo.voxmetriks.local"),
)

_LISTENER_FREE_USERNAME = "listener.free"
_PENDING_INVITE_EMAIL = "household.pending@demo.voxmetriks.local"


def _demo_password() -> str:
    return (
        os.environ.get("DEMO_ACCOUNT_PASSWORD")
        or os.environ.get("DEMO_PASSWORD")
        or os.environ.get("VOXMETRIKS_DEMO_PASSWORD")
        or "demo-change-me"
    )


def _ensure_user(conn: duckdb.DuckDBPyConnection, username: str, email: str) -> int:
    ensure_user_tables(conn)
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ?", [email.lower()]
    ).fetchone()
    if row:
        return int(row[0])
    from app.packages.identity.services.user_service import _insert_user

    _insert_user(
        conn,
        username=username,
        email=email,
        password_hash=hash_password(_demo_password()),
        favorite_genre=None,
        email_verified=True,
        auth_provider="local",
    )
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ?", [email.lower()]
    ).fetchone()
    return int(row[0])


def _normalize_listener_free(conn: duckdb.DuckDBPyConnection, user_id: int) -> None:
    """Force the presentation Free account back to a single active personal_free.

    Cancels non-free subscriptions in active/past_due/processing via use cases.
    Paid invoices and personal library data are left intact. Runs in one transaction.
    """
    with transactional(conn):
        while True:
            try:
                cancel_subscription(conn, user_id, at_period_end=False)
            except PersonalNotFoundError:
                break
        ensure_free_subscription(conn, user_id)
        free_active = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM personal_subscription s
                JOIN personal_plan p ON p.id = s.plan_id
                WHERE s.user_id = ?
                  AND p.code = 'personal_free'
                  AND s.status = 'active'
                """,
                [user_id],
            ).fetchone()[0]
        )
        if free_active != 1:
            raise RuntimeError(
                "Demo listener.free must resolve to exactly one active personal_free"
            )
        premium_left = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM personal_subscription s
                JOIN personal_plan p ON p.id = s.plan_id
                WHERE s.user_id = ?
                  AND p.is_free = FALSE
                  AND s.status IN ('active', 'past_due', 'processing')
                """,
                [user_id],
            ).fetchone()[0]
        )
        if premium_left != 0:
            raise RuntimeError(
                "Demo listener.free still has non-free subscriptions after normalize"
            )


def _ensure_pending_demo_invitation(
    conn: duckdb.DuckDBPyConnection, owner_user_id: int
) -> None:
    """Keep exactly one non-expired pending invite for the demo pending email."""
    email_n = _PENDING_INVITE_EMAIL
    with transactional(conn):
        hh = get_household(conn, owner_user_id)
        if not hh or hh.get("my_role") != "owner":
            raise RuntimeError("Demo household owner required for pending invite")

        now = utc_now()
        rows = conn.execute(
            """
            SELECT hi.id, hi.expires_at
            FROM household_invitation hi
            JOIN household h ON h.id = hi.household_id
            WHERE h.owner_user_id = ?
              AND hi.email_normalized = ?
              AND hi.status = 'pending'
            ORDER BY hi.id ASC
            """,
            [owner_user_id, email_n],
        ).fetchall()

        valid_ids: list[int] = []
        for inv_id, expires_at in rows:
            if expires_at is not None and expires_at <= now:
                conn.execute(
                    """
                    UPDATE household_invitation
                    SET status = 'expired', updated_at = ?
                    WHERE id = ?
                    """,
                    [now, int(inv_id)],
                )
            else:
                # Keep oldest valid pending (ORDER BY id ASC); extras → canceled.
                valid_ids.append(int(inv_id))

        if valid_ids:
            for extra_id in valid_ids[1:]:
                conn.execute(
                    """
                    UPDATE household_invitation
                    SET status = 'canceled', updated_at = ?
                    WHERE id = ?
                    """,
                    [now, extra_id],
                )
        else:
            if int(hh.get("seats_available") or 0) <= 0:
                raise RuntimeError(
                    "Demo pending invite requires available household seats"
                )
            invite_member(conn, owner_user_id, email_n)

        pending_valid = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM household_invitation hi
                JOIN household h ON h.id = hi.household_id
                WHERE h.owner_user_id = ?
                  AND hi.email_normalized = ?
                  AND hi.status = 'pending'
                  AND hi.expires_at > ?
                """,
                [owner_user_id, email_n, now],
            ).fetchone()[0]
        )
        if pending_valid != 1:
            raise RuntimeError(
                "Demo pending invite postcondition failed: "
                f"expected exactly 1 valid pending, got {pending_valid}"
            )


def seed_personal_demo(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """Create demo personal subscribers. Safe to re-run."""
    ensure_personal_subscription_tables(conn)
    ids: Dict[str, int] = {}
    for username, email in DEMO_ACCOUNTS:
        ids[username] = _ensure_user(conn, username, email)
        ensure_free_subscription(conn, ids[username])

    _normalize_listener_free(conn, ids[_LISTENER_FREE_USERNAME])

    # Premium individual
    prem = ids["listener.premium"]
    sub = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'premium_individual' AND s.status = 'active'
        """,
        [prem],
    ).fetchone()
    if not sub:
        checkout = start_checkout(
            conn, prem, plan_code="premium_individual", billing_period="monthly"
        )
        simulate_payment(
            conn, prem, attempt_id=checkout["attempt_id"], scenario="succeeded"
        )

    # Familiar owner + members (canonical household.owner = Familiar)
    owner = ids["household.owner"]
    member = ids["household.member"]
    fam = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'premium_family' AND s.status = 'active'
        """,
        [owner],
    ).fetchone()
    if not fam:
        checkout = start_checkout(
            conn, owner, plan_code="premium_family", billing_period="monthly"
        )
        simulate_payment(
            conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
        )
    hh = conn.execute(
        """
        SELECT 1 FROM household_member
        WHERE user_id = ? AND status = 'active' AND role = 'member'
        """,
        [member],
    ).fetchone()
    if not hh:
        inv = invite_member(conn, owner, "household.member@demo.voxmetriks.local")
        accept_invitation(conn, member, inv["token"])

    # Extra family members on household.owner (canonical member2 + member3)
    email_map = {u: e for u, e in DEMO_ACCOUNTS}
    for uname in ("household.member2", "household.member3"):
        uid = ids[uname]
        already = conn.execute(
            """
            SELECT 1 FROM household_member hm
            JOIN household h ON h.id = hm.household_id
            WHERE hm.user_id = ? AND hm.status = 'active' AND h.owner_user_id = ?
            """,
            [uid, owner],
        ).fetchone()
        if not already:
            inv = invite_member(conn, owner, email_map[uname])
            accept_invitation(conn, uid, inv["token"])

    _ensure_pending_demo_invitation(conn, owner)

    # Past due + declined attempt
    pd = ids["listener.pastdue"]
    past = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status = 'past_due'
        """,
        [pd],
    ).fetchone()
    if not past:
        checkout = start_checkout(
            conn, pd, plan_code="premium_individual", billing_period="monthly"
        )
        simulate_payment(
            conn, pd, attempt_id=checkout["attempt_id"], scenario="declined"
        )

    return {
        "ok": True,
        "demo": True,
        "accounts": [
            {"username": u, "email": e, "user_id": ids.get(u)}
            for u, e in DEMO_ACCOUNTS
        ],
        "note": "Passwords from DEMO_ACCOUNT_PASSWORD / DEMO_PASSWORD env only.",
        "seeded_at": utc_now().isoformat(),
    }
