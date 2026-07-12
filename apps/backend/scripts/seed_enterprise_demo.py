"""Optional enterprise demo seed — Spec 028.

Run explicitly only when ``VOXMETRIKS_SEED_ENTERPRISE_DEMO=1``:

    VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py

Never executes on import. All records are synthetic and marked ``is_demo``.
Safe when tables are missing (skips gracefully).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_DEMO_BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║  VOXMETRIKS ENTERPRISE DEMO SEED — SYNTHETIC / ACADEMIC DATA     ║
║  All records marked is_demo. Not for production or compliance.    ║
╚══════════════════════════════════════════════════════════════════╝
"""


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and row[0] > 0)


def _next_id(conn, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def seed_enterprise_demo() -> dict[str, object]:
    """Insert synthetic demo org + plan/subscription stubs when tables exist."""
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    result: dict[str, object] = {
        "seeded": False,
        "organization_id": None,
        "plan_id": None,
        "subscription_id": None,
        "skipped": [],
    }

    with using_write_conn() as conn:
        now = utc_now()

        if not _table_exists(conn, "app_user"):
            result["skipped"].append("app_user")
            return result

        admin = conn.execute(
            "SELECT id FROM app_user WHERE username = 'admin' OR email LIKE '%admin%' LIMIT 1"
        ).fetchone()
        if not admin:
            result["skipped"].append("admin_user")
            return result
        admin_id = int(admin[0])

        org_id: int | None = None
        if _table_exists(conn, "app_organization"):
            existing = conn.execute(
                "SELECT id FROM app_organization WHERE slug = 'enterprise-demo-s028'"
            ).fetchone()
            if existing:
                org_id = int(existing[0])
            else:
                org_id = _next_id(conn, "app_organization")
                conn.execute(
                    """
                    INSERT INTO app_organization
                        (id, display_name, slug, organization_type, country_code, timezone,
                         default_currency, status, created_by, created_at, updated_at, is_demo)
                    VALUES (?, 'Enterprise Demo Org (Synthetic)', 'enterprise-demo-s028',
                            'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?, TRUE)
                    """,
                    [org_id, admin_id, now, now],
                )
            result["organization_id"] = org_id

            if _table_exists(conn, "app_organization_member"):
                member = conn.execute(
                    "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
                    [org_id, admin_id],
                ).fetchone()
                if not member:
                    mid = _next_id(conn, "app_organization_member")
                    conn.execute(
                        """
                        INSERT INTO app_organization_member
                            (id, organization_id, user_id, status, created_by, created_at, updated_at)
                        VALUES (?, ?, ?, 'active', ?, ?, ?)
                        """,
                        [mid, org_id, admin_id, admin_id, now, now],
                    )
                    if _table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role"):
                        owner = conn.execute(
                            "SELECT id FROM app_business_role WHERE code = 'owner'"
                        ).fetchone()
                        if owner:
                            mrid = _next_id(conn, "app_member_role")
                            conn.execute(
                                """
                                INSERT INTO app_member_role
                                    (id, member_id, role_id, status, assigned_by, assigned_at)
                                VALUES (?, ?, ?, 'active', ?, ?)
                                """,
                                [mrid, mid, int(owner[0]), admin_id, now],
                            )
        else:
            result["skipped"].append("app_organization")

        plan_id: int | None = None
        if _table_exists(conn, "app_plan"):
            plan_row = conn.execute(
                "SELECT id FROM app_plan WHERE code = 'demo-enterprise-starter'"
            ).fetchone()
            if plan_row:
                plan_id = int(plan_row[0])
            else:
                plan_id = _next_id(conn, "app_plan")
                conn.execute(
                    """
                    INSERT INTO app_plan
                        (id, code, display_name, description, status, trial_days_default,
                         sort_order, created_at, updated_at)
                    VALUES (?, 'demo-enterprise-starter', 'Demo Enterprise Starter',
                            '[SYNTHETIC] Academic demo plan — not a commercial offer.',
                            'active', 14, 0, ?, ?)
                    """,
                    [plan_id, now, now],
                )
            result["plan_id"] = plan_id

            if _table_exists(conn, "app_plan_price"):
                if not conn.execute(
                    "SELECT 1 FROM app_plan_price WHERE plan_id = ? AND currency = 'USD'",
                    [plan_id],
                ).fetchone():
                    price_id = _next_id(conn, "app_plan_price")
                    conn.execute(
                        """
                        INSERT INTO app_plan_price
                            (id, plan_id, currency, billing_period, amount, status, created_at, updated_at)
                        VALUES (?, ?, 'USD', 'monthly', 0.00, 'active', ?, ?)
                        """,
                        [price_id, plan_id, now, now],
                    )
        else:
            result["skipped"].append("app_plan")

        if (
            org_id is not None
            and plan_id is not None
            and _table_exists(conn, "app_subscription")
        ):
            sub_row = conn.execute(
                "SELECT id FROM app_subscription WHERE organization_id = ? AND plan_id = ?",
                [org_id, plan_id],
            ).fetchone()
            if sub_row:
                result["subscription_id"] = int(sub_row[0])
            else:
                sub_id = _next_id(conn, "app_subscription")
                conn.execute(
                    """
                    INSERT INTO app_subscription
                        (id, organization_id, plan_id, status, billing_currency,
                         activation_source, access_state, created_at, updated_at)
                    VALUES (?, ?, ?, 'trialing', 'USD', 'demo_seed_synthetic', 'full', ?, ?)
                    """,
                    [sub_id, org_id, plan_id, now, now],
                )
                result["subscription_id"] = sub_id
        elif not _table_exists(conn, "app_subscription"):
            result["skipped"].append("app_subscription")

        result["seeded"] = org_id is not None

    return result


def main() -> int:
    if os.getenv("VOXMETRIKS_SEED_ENTERPRISE_DEMO", "").strip() not in ("1", "true", "yes", "on"):
        print(
            "Enterprise demo seed skipped. Set VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 to run.",
            file=sys.stderr,
        )
        return 0

    print(_DEMO_BANNER)
    outcome = seed_enterprise_demo()
    if outcome["seeded"]:
        print("DEMO seed complete (synthetic):")
        print(f"  organization_id={outcome['organization_id']}")
        print(f"  plan_id={outcome['plan_id']}")
        print(f"  subscription_id={outcome['subscription_id']}")
    else:
        print("DEMO seed: nothing inserted.", outcome.get("skipped"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
