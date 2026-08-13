"""One-shot validation for release dataset (no pytest)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

SLUGS = (
    "aurora-records",
    "nexus-media",
    "pulse-latam",
    "verde-sonora",
    "costa-pacific",
)


def main() -> int:
    from app.core.database import using_write_conn

    with using_write_conn() as conn:
        orgs = conn.execute(
            "SELECT id, slug, display_name FROM app_organization WHERE slug IN (?,?,?,?,?)",
            list(SLUGS),
        ).fetchall()
        org_map = {int(r[0]): {"slug": r[1], "name": r[2]} for r in orgs}
        ids = list(org_map.keys())

        def count(sql: str, params=None) -> int:
            row = conn.execute(sql, params or []).fetchone()
            return int(row[0] or 0)

        def group(sql: str, params=None) -> list:
            return conn.execute(sql, params or []).fetchall()

        report = {
            "organizations": [{"id": i, **org_map[i]} for i in ids],
            "users_synthetic": count(
                "SELECT COUNT(*) FROM app_user WHERE email LIKE '%@voxmetriks.studio.local'"
            ),
            "memberships": count(
                "SELECT COUNT(*) FROM app_organization_member WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "campaigns": count(
                "SELECT COUNT(*) FROM app_campaign WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "opportunities": count(
                "SELECT COUNT(*) FROM app_crm_opportunity WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "invoices": count(
                "SELECT COUNT(*) FROM app_invoice WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "payments": count(
                "SELECT COUNT(*) FROM app_payment WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "subscriptions": count(
                "SELECT COUNT(*) FROM app_subscription WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "releases": count(
                "SELECT COUNT(*) FROM app_release_submission WHERE idempotency_key LIKE 'rf-final-rel-%'"
            ),
            "rights_contracts": count(
                "SELECT COUNT(*) FROM app_rights_contract WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "rights_conflicts": count(
                "SELECT COUNT(*) FROM app_rights_conflict WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "support_cases": count(
                "SELECT COUNT(*) FROM app_support_case WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "alerts": count(
                "SELECT COUNT(*) FROM app_business_alert WHERE organization_id IN (?,?,?,?,?)",
                ids,
            ),
            "jobs": count(
                "SELECT COUNT(*) FROM app_background_job WHERE job_code LIKE 'rf-final-%'"
            ),
            "job_executions": count(
                "SELECT COUNT(*) FROM app_job_execution WHERE result_json LIKE 'rf-final-exec-%'"
            ),
            "personal_subscriptions": count(
                """
                SELECT COUNT(*) FROM personal_subscription ps
                JOIN app_user u ON u.id = ps.user_id
                WHERE u.email LIKE '%@voxmetriks.studio.local'
                """
            ),
            "stream_months": count(
                """
                SELECT COUNT(DISTINCT strftime(fecha, '%Y-%m'))
                FROM agg_daily_streams
                WHERE fecha >= CURRENT_DATE - INTERVAL 370 DAY
                """
            ),
            "by_org": {},
            "isolation": {
                "release_cross_org": count(
                    """
                    SELECT COUNT(*) FROM app_release_submission
                    WHERE idempotency_key LIKE 'rf-final-rel-%'
                      AND organization_id NOT IN (?,?,?,?,?)
                    """,
                    ids,
                ),
                "campaign_demo_names": count(
                    """
                    SELECT COUNT(*) FROM app_campaign
                    WHERE organization_id IN (?,?,?,?,?)
                      AND (name ILIKE '%demo%' OR name ILIKE '%fixture%')
                    """,
                    ids,
                ),
            },
            "personal_ok": True,
        }

        demo = conn.execute(
            """
            SELECT id, username, preferences_json
            FROM app_user
            WHERE LOWER(email)='demo@voxmetrik.io' OR LOWER(username)='demo'
            LIMIT 1
            """
        ).fetchone()
        if demo:
            prefs = str(demo[2] or "")
            if "voxmetriks-release-final-2026" in prefs:
                report["personal_ok"] = False
            for oid in ids:
                mem = conn.execute(
                    """
                    SELECT 1 FROM app_organization_member
                    WHERE organization_id = ? AND user_id = ?
                    """,
                    [oid, int(demo[0])],
                ).fetchone()
                if mem:
                    report["personal_ok"] = False

        for oid, meta in org_map.items():
            report["by_org"][meta["slug"]] = {
                "display_name": meta["name"],
                "campaigns": count(
                    "SELECT COUNT(*) FROM app_campaign WHERE organization_id = ?", [oid]
                ),
                "opportunities": count(
                    "SELECT COUNT(*) FROM app_crm_opportunity WHERE organization_id = ?",
                    [oid],
                ),
                "invoices": count(
                    "SELECT COUNT(*) FROM app_invoice WHERE organization_id = ?", [oid]
                ),
                "payments": count(
                    "SELECT COUNT(*) FROM app_payment WHERE organization_id = ?", [oid]
                ),
                "subscriptions": count(
                    "SELECT COUNT(*) FROM app_subscription WHERE organization_id = ?",
                    [oid],
                ),
                "releases": count(
                    """
                    SELECT COUNT(*) FROM app_release_submission
                    WHERE organization_id = ? AND idempotency_key LIKE 'rf-final-rel-%'
                    """,
                    [oid],
                ),
                "rights_contracts": count(
                    "SELECT COUNT(*) FROM app_rights_contract WHERE organization_id = ?",
                    [oid],
                ),
                "rights_conflicts": count(
                    "SELECT COUNT(*) FROM app_rights_conflict WHERE organization_id = ?",
                    [oid],
                ),
                "support_cases": count(
                    "SELECT COUNT(*) FROM app_support_case WHERE organization_id = ?",
                    [oid],
                ),
                "alerts": count(
                    "SELECT COUNT(*) FROM app_business_alert WHERE organization_id = ?",
                    [oid],
                ),
                "members": count(
                    "SELECT COUNT(*) FROM app_organization_member WHERE organization_id = ?",
                    [oid],
                ),
            }

        print(json.dumps(report, indent=2, default=str))
        ok = (
            report["personal_ok"]
            and report["isolation"]["release_cross_org"] == 0
            and report["isolation"]["campaign_demo_names"] == 0
            and report["organizations"]
            and len(report["organizations"]) == 5
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
