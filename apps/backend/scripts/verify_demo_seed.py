"""Verify integrated demo seed (no passwords printed)."""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.database import using_write_conn


def main() -> None:
    with using_write_conn() as c:
        bad = c.execute(
            """
            SELECT display_name, slug FROM app_organization
            WHERE LOWER(COALESCE(display_name, '')) LIKE '%golden%'
               OR LOWER(COALESCE(display_name, '')) LIKE '%gp plan%'
               OR LOWER(COALESCE(display_name, '')) LIKE '%stagetest%'
               OR LOWER(COALESCE(display_name, '')) LIKE '%other org%'
               OR LOWER(COALESCE(display_name, '')) LIKE '%api acme%'
               OR LOWER(COALESCE(slug, '')) LIKE 'gp-%'
            """
        ).fetchall()
        print("pollution_orgs", bad)
        plans = c.execute(
            """
            SELECT code, display_name, status FROM app_plan
            WHERE status != 'archived' AND (
              LOWER(code) LIKE 'gp-%'
              OR LOWER(display_name) LIKE '%gp plan%'
              OR LOWER(display_name) LIKE '%golden%'
            )
            """
        ).fetchall()
        print("active_test_plans", plans)
        users = c.execute(
            """
            SELECT username FROM app_user
            WHERE username IN (
              'listener.free','listener.premium','household.owner','household.member',
              'platform.admin','sales.manager','organization.owner','finance.manager'
            )
            ORDER BY username
            """
        ).fetchall()
        print("demo_users", [u[0] for u in users])
        fam = c.execute(
            """
            SELECT p.code, s.status FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            JOIN app_user u ON u.id = s.user_id
            WHERE u.username = 'household.owner' AND s.status = 'active'
            """
        ).fetchall()
        print("household_owner_plan", fam)
        counts = c.execute(
            """
            SELECT COUNT(*) FROM dim_track
            """
        ).fetchone()
        print("dim_track_count", int(counts[0]) if counts else None)


if __name__ == "__main__":
    main()
