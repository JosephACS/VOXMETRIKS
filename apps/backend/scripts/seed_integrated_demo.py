"""Integrated VOXMETRIKS demo accounts — final closure after Spec 029.

Creates the seven local demo identities used for B2C + B2B demonstrations.
Opt-in only. Idempotent. Never prints the password.

Password (hash only stored):
  DEMO_ACCOUNT_PASSWORD  (preferred)
  DEMO_PASSWORD / VOXMETRIKS_DEMO_PASSWORD  (legacy fallback)

Run (from apps/backend):

    set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
    set DEMO_ACCOUNT_PASSWORD=your-local-secret
    python scripts/seed_integrated_demo.py

Optional cleanup of pytest / Golden Path pollution first:

    python scripts/seed_integrated_demo.py --cleanup-first

Does not touch music warehouse tables (dim_*/fact_*).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

ORG_SLUG = "voxmetriks-demo"
ORG_DISPLAY = "VOXMETRIKS Demo"

# username -> email
DEMO_USERS: tuple[tuple[str, str], ...] = (
    ("listener.free", "listener.free@demo.voxmetriks.local"),
    ("listener.premium", "listener.premium@demo.voxmetriks.local"),
    ("household.owner", "household.owner@demo.voxmetriks.local"),
    ("household.member", "household.member@demo.voxmetriks.local"),
    ("household.member2", "household.member2@demo.voxmetriks.local"),
    ("platform.admin", "platform.admin@demo.voxmetriks.local"),
    ("sales.manager", "sales.manager@demo.voxmetriks.local"),
    ("organization.owner", "organization.owner@demo.voxmetriks.local"),
    ("finance.manager", "finance.manager@demo.voxmetriks.local"),
)


def _demo_password() -> str:
    return (
        os.environ.get("DEMO_ACCOUNT_PASSWORD")
        or os.environ.get("DEMO_PASSWORD")
        or os.environ.get("VOXMETRIKS_DEMO_PASSWORD")
        or "demo-change-me"
    )


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and row[0])


def _has_column(conn, table: str, column: str) -> bool:
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return column in cols
    except Exception:
        return False


def _next_id(conn, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _ensure_user(conn, username: str, email: str) -> int:
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ? OR LOWER(username) = ?",
        [email.lower(), username.lower()],
    ).fetchone()
    prefs = json.dumps(
        {
            "demo": True,
            "dark_mode": True,
            "language": "es",
            "recommendations_enabled": True,
        }
    )
    pwd_hash = hash_password(_demo_password())
    now = utc_now()
    if row:
        uid = int(row[0])
        # Avoid rewriting unique username/email (DuckDB UPDATE quirks on unique idxs).
        conn.execute(
            """
            UPDATE app_user
            SET password_hash = ?,
                preferences_json = ?,
                email_verified = TRUE,
                auth_provider = 'local'
            WHERE id = ?
            """,
            [pwd_hash, prefs, uid],
        )
        return uid

    uid = _next_id(conn, "app_user")
    cols = (
        "id, username, email, password_hash, role, plan, favorite_genre, "
        "created_at, preferences_json, email_verified, auth_provider"
    )
    conn.execute(
        f"""
        INSERT INTO app_user ({cols})
        VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, ?, TRUE, 'local')
        """,
        [uid, username, email, pwd_hash, now, prefs],
    )
    return uid


def _assign_platform_role(conn, user_id: int, role_code: str) -> None:
    from app.packages.platform_rbac.infrastructure.schema import (
        _assign_platform_role_if_missing,
        ensure_platform_rbac_tables,
    )
    from app.core.time_util import utc_now

    ensure_platform_rbac_tables(conn)
    _assign_platform_role_if_missing(
        conn, user_id=user_id, role_code=role_code, now=utc_now()
    )


def _ensure_org_member(conn, org_id: int, user_id: int, role_codes: list[str]) -> None:
    from app.core.time_util import utc_now
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables

    ensure_organization_tables(conn)
    now = utc_now()
    member = conn.execute(
        "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
        [org_id, user_id],
    ).fetchone()
    if member:
        member_id = int(member[0])
        conn.execute(
            "UPDATE app_organization_member SET status = 'active', updated_at = ? WHERE id = ?",
            [now, member_id],
        )
    else:
        member_id = _next_id(conn, "app_organization_member")
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [member_id, org_id, user_id, user_id, now, now],
        )

    if not (
        _table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role")
    ):
        return
    for code in role_codes:
        role = conn.execute(
            "SELECT id FROM app_business_role WHERE code = ?", [code]
        ).fetchone()
        if not role:
            continue
        role_id = int(role[0])
        exists = conn.execute(
            """
            SELECT 1 FROM app_member_role
            WHERE member_id = ? AND role_id = ? AND status = 'active'
            """,
            [member_id, role_id],
        ).fetchone()
        if exists:
            continue
        mrid = _next_id(conn, "app_member_role")
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            [mrid, member_id, role_id, user_id, now],
        )


def _ensure_canonical_org(conn, created_by: int) -> int:
    from app.core.time_util import utc_now
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables

    ensure_organization_tables(conn)
    now = utc_now()
    row = conn.execute(
        "SELECT id FROM app_organization WHERE slug = ?", [ORG_SLUG]
    ).fetchone()
    if row:
        org_id = int(row[0])
        sets = [
            "display_name = ?",
            "status = 'active'",
            "updated_at = ?",
            "timezone = 'America/Guayaquil'",
            "default_currency = 'USD'",
        ]
        params: list[Any] = [ORG_DISPLAY, now]
        if _has_column(conn, "app_organization", "is_demo"):
            sets.append("is_demo = TRUE")
        if _has_column(conn, "app_organization", "is_test"):
            sets.append("is_test = FALSE")
        if _has_column(conn, "app_organization", "country_code"):
            sets.append("country_code = 'EC'")
        conn.execute(
            f"UPDATE app_organization SET {', '.join(sets)} WHERE id = ?",
            [*params, org_id],
        )
        return org_id

    org_id = _next_id(conn, "app_organization")
    cols = (
        "id, display_name, slug, organization_type, country_code, timezone, "
        "default_currency, status, created_by, created_at, updated_at"
    )
    vals = "?, ?, ?, 'label', 'EC', 'America/Guayaquil', 'USD', 'active', ?, ?, ?"
    params = [org_id, ORG_DISPLAY, ORG_SLUG, created_by, now, now]
    if _has_column(conn, "app_organization", "is_demo"):
        cols += ", is_demo"
        vals += ", TRUE"
    if _has_column(conn, "app_organization", "is_test"):
        cols += ", is_test"
        vals += ", FALSE"
    conn.execute(f"INSERT INTO app_organization ({cols}) VALUES ({vals})", params)
    return org_id


def _seed_personal_line(conn, ids: dict[str, int]) -> dict[str, Any]:
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        ensure_free_subscription,
        invite_member,
        simulate_payment,
        start_checkout,
    )
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )

    ensure_personal_subscription_tables(conn)
    for uname in (
        "listener.free",
        "listener.premium",
        "household.owner",
        "household.member",
        "household.member2",
    ):
        ensure_free_subscription(conn, ids[uname])

    # Premium Individual
    prem = ids["listener.premium"]
    active = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'premium_individual' AND s.status = 'active'
        """,
        [prem],
    ).fetchone()
    if not active:
        checkout = start_checkout(
            conn, prem, plan_code="premium_individual", billing_period="monthly"
        )
        simulate_payment(
            conn, prem, attempt_id=checkout["attempt_id"], scenario="succeeded"
        )

    # Familiar titular + members (Spec closure: household.owner = Familiar)
    owner = ids["household.owner"]
    fam = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'premium_family' AND s.status = 'active'
        """,
        [owner],
    ).fetchone()
    if not fam:
        # If previously seeded as Duo, still allow family checkout path once
        duo = conn.execute(
            """
            SELECT s.id FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            WHERE s.user_id = ? AND p.code IN ('premium_duo', 'premium_family')
              AND s.status IN ('active', 'past_due', 'canceled')
            """,
            [owner],
        ).fetchone()
        if not duo:
            checkout = start_checkout(
                conn, owner, plan_code="premium_family", billing_period="monthly"
            )
            simulate_payment(
                conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
            )
        else:
            # Upgrade via new checkout when only duo exists
            still_family = conn.execute(
                """
                SELECT s.id FROM personal_subscription s
                JOIN personal_plan p ON p.id = s.plan_id
                WHERE s.user_id = ? AND p.code = 'premium_family' AND s.status = 'active'
                """,
                [owner],
            ).fetchone()
            if not still_family:
                checkout = start_checkout(
                    conn, owner, plan_code="premium_family", billing_period="monthly"
                )
                simulate_payment(
                    conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
                )

    email_map = {u: e for u, e in DEMO_USERS}
    for member_key in ("household.member", "household.member2"):
        mid = ids[member_key]
        already = conn.execute(
            """
            SELECT 1 FROM household_member hm
            JOIN household h ON h.id = hm.household_id
            WHERE hm.user_id = ? AND hm.status = 'active' AND h.owner_user_id = ?
            """,
            [mid, owner],
        ).fetchone()
        if not already:
            try:
                inv = invite_member(conn, owner, email_map[member_key])
                accept_invitation(conn, mid, inv["token"])
            except Exception:
                pass

    return {"personal_ok": True}


def _ensure_professional_subscription(conn, org_id: int, actor_id: int) -> None:
    """Attach Professional plan to canonical demo org when missing."""
    from app.core.time_util import utc_now
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    ensure_subscription_tables(conn)
    if not _table_exists(conn, "app_plan") or not _table_exists(conn, "app_subscription"):
        return
    plan = conn.execute(
        "SELECT id FROM app_plan WHERE code = 'professional' AND status != 'archived' LIMIT 1"
    ).fetchone()
    if not plan:
        return
    plan_id = int(plan[0])
    existing = conn.execute(
        """
        SELECT id FROM app_subscription
        WHERE organization_id = ? AND status IN ('active', 'trialing', 'past_due')
        LIMIT 1
        """,
        [org_id],
    ).fetchone()
    if existing:
        return
    price = conn.execute(
        """
        SELECT id FROM app_plan_price
        WHERE plan_id = ? AND billing_period = 'monthly' AND status = 'active'
        LIMIT 1
        """,
        [plan_id],
    ).fetchone()
    price_id = int(price[0]) if price else None
    now = utc_now()
    sid = _next_id(conn, "app_subscription")
    cols = "id, organization_id, plan_id, status, created_at, updated_at"
    vals = "?, ?, ?, 'active', ?, ?"
    params: list[Any] = [sid, org_id, plan_id, now, now]
    if price_id is not None and _has_column(conn, "app_subscription", "plan_price_id"):
        cols += ", plan_price_id"
        vals += ", ?"
        params.append(price_id)
    if _has_column(conn, "app_subscription", "created_by"):
        cols += ", created_by"
        vals += ", ?"
        params.append(actor_id)
    try:
        conn.execute(f"INSERT INTO app_subscription ({cols}) VALUES ({vals})", params)
    except Exception:
        pass


def seed_integrated_demo() -> dict[str, Any]:
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    report: dict[str, Any] = {
        "ok": False,
        "demo": True,
        "accounts": [],
        "organization_slug": ORG_SLUG,
        "password_env": "DEMO_ACCOUNT_PASSWORD",
        "seeded_at": None,
    }

    with using_write_conn() as conn:
        ensure_platform_rbac_tables(conn)
        ensure_subscription_tables(conn)
        ids: dict[str, int] = {}
        for username, email in DEMO_USERS:
            ids[username] = _ensure_user(conn, username, email)

        _assign_platform_role(conn, ids["platform.admin"], "platform_admin")
        _assign_platform_role(conn, ids["sales.manager"], "sales_manager")

        org_id = _ensure_canonical_org(conn, ids["organization.owner"])
        _ensure_org_member(conn, org_id, ids["organization.owner"], ["owner"])
        # billing_manager: invoices, payments, refunds, credit notes — not global plans
        _ensure_org_member(
            conn, org_id, ids["finance.manager"], ["billing_manager", "finance"]
        )
        _ensure_professional_subscription(conn, org_id, ids["organization.owner"])
        personal = _seed_personal_line(conn, ids)

        report["ok"] = True
        report["organization_id"] = org_id
        report["personal"] = personal
        report["accounts"] = [
            {
                "username": u,
                "email": e,
                "user_id": ids[u],
                "demo": True,
                "email_verified": True,
            }
            for u, e in DEMO_USERS
        ]
        report["seeded_at"] = utc_now().isoformat()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed integrated VOXMETRIKS demo accounts")
    parser.add_argument(
        "--cleanup-first",
        action="store_true",
        help="Run cleanup_test_organizations.py --apply --retire-test-plans first",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if os.environ.get("VOXMETRIKS_SEED_DEMO_ACCOUNTS", "").strip() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        msg = (
            "Refusing to seed: set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1 "
            "and DEMO_ACCOUNT_PASSWORD before running."
        )
        print(msg)
        return 2

    if args.cleanup_first:
        import subprocess

        cleanup = _BACKEND / "scripts" / "cleanup_test_organizations.py"
        subprocess.run(
            [
                sys.executable,
                str(cleanup),
                "--apply",
                "--retire-test-plans",
                "--json",
            ],
            cwd=str(_BACKEND),
            check=False,
        )

    report = seed_integrated_demo()
    # Never include password
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("Integrated demo seed complete.")
        print(f"  organization: {report.get('organization_slug')}")
        print(f"  accounts: {len(report.get('accounts') or [])}")
        print("  password: from DEMO_ACCOUNT_PASSWORD (not printed)")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
