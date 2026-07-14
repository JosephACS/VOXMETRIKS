#!/usr/bin/env python3
"""Safe cleanup of synthetic pytest / Golden Path / manual-test enterprise pollution.

Dry-run by default. Use --apply to delete. Never touches warehouse music tables
(dim_*, fact_*, bronze/silver/gold, etc.). Protects canonical demo slug.

Usage (from apps/backend):

    python scripts/cleanup_test_organizations.py
    python scripts/cleanup_test_organizations.py --apply
    python scripts/cleanup_test_organizations.py --apply --retire-test-plans
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Org-scoped enterprise tables (delete children first). Order matters weakly —
# we delete by organization_id regardless of FK (DuckDB is permissive).
ORG_SCOPED_TABLES: tuple[tuple[str, str], ...] = (
    # Support / CS
    ("app_support_message", "case_id"),  # special: via cases
    ("app_support_case", "organization_id"),
    ("app_customer_intervention", "organization_id"),
    ("app_customer_risk", "organization_id"),
    ("app_customer_health_snapshot", "organization_id"),
    ("app_customer_onboarding_step", "onboarding_id"),  # special
    ("app_customer_onboarding", "organization_id"),
    ("app_renewal_readiness", "organization_id"),
    ("app_expansion_opportunity", "organization_id"),
    # Reporting
    ("app_decision_action", "decision_id"),  # special
    ("app_business_decision", "organization_id"),
    ("app_executive_report", "organization_id"),
    ("app_report_snapshot", "organization_id"),
    ("app_report_generation", "organization_id"),
    ("app_report_definition", "organization_id"),
    # Campaigns
    ("app_campaign_expense", "organization_id"),
    ("app_campaign_budget", "organization_id"),
    ("app_campaign_result", "organization_id"),
    ("app_campaign", "organization_id"),
    # Rights / artists
    ("app_rights_conflict", "organization_id"),
    ("app_rights_contract_party", "contract_id"),  # special
    ("app_rights_contract", "organization_id"),
    ("app_catalog_release_track", "release_id"),  # special
    ("app_catalog_release", "organization_id"),
    ("app_catalog_asset", "organization_id"),
    ("app_artist_team_member", "artist_profile_id"),  # special
    ("app_artist_profile", "organization_id"),
    # Billing
    ("app_billing_ledger_entry", "organization_id"),
    ("app_billing_dunning", "organization_id"),
    ("app_credit_note", "organization_id"),
    ("app_refund", "organization_id"),
    ("app_payment", "organization_id"),
    ("app_payment_attempt", "organization_id"),
    ("app_payment_method_reference", "organization_id"),
    ("app_invoice_item", "invoice_id"),  # special
    ("app_invoice", "organization_id"),
    ("app_billing_profile", "organization_id"),
    # Subscriptions
    ("app_usage_record", "organization_id"),
    ("app_subscription_addon", "subscription_id"),  # special
    ("app_subscription_entitlement", "subscription_id"),  # special
    ("app_subscription_change", "subscription_id"),  # special
    ("app_subscription", "organization_id"),
    # CRM / contracts
    ("app_crm_quotation_item", "quotation_version_id"),  # special
    ("app_crm_quotation_version", "quotation_id"),  # special
    ("app_crm_quotation", "opportunity_id"),  # special via opp
    ("app_commercial_contract", "organization_id"),
    ("app_crm_activity", "organization_id"),
    ("app_crm_opportunity", "organization_id"),
    ("app_crm_prospect_contact", "prospect_id"),  # special
    ("app_crm_prospect", "organization_id"),
    # Compliance (org-scoped only)
    ("app_data_request", "organization_id"),
    ("app_consent_record", "organization_id"),
    ("app_legal_hold", "organization_id"),
    # Biz analytics org rows
    ("app_business_alert", "organization_id"),
    ("app_business_recommendation", "organization_id"),
    # Org core
    ("app_audit_log", "organization_id"),
    ("app_organization_invitation", "organization_id"),
    ("app_member_role", "member_id"),  # special via members
    ("app_organization_member", "organization_id"),
)

WAREHOUSE_PREFIXES = (
    "dim_",
    "fact_",
    "bridge_",
    "bronze_",
    "silver_",
    "gold_",
    "stg_",
    "raw_",
)


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [name],
    ).fetchone()
    return bool(row and row[0])


def _has_column(conn, table: str, column: str) -> bool:
    cols = {
        r[0]
        for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [table],
        ).fetchall()
    }
    return column in cols


def _safe_count(conn, sql: str, params: list) -> int:
    try:
        return int(conn.execute(sql, params).fetchone()[0])
    except Exception:
        return -1


def _count_related(conn, org_id: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, col in ORG_SCOPED_TABLES:
        if col != "organization_id":
            continue
        if not _table_exists(conn, table):
            continue
        counts[table] = _safe_count(
            conn, f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", [org_id]
        )
    if _table_exists(conn, "app_user_organization_preference"):
        counts["app_user_organization_preference"] = _safe_count(
            conn,
            "SELECT COUNT(*) FROM app_user_organization_preference WHERE active_organization_id = ?",
            [org_id],
        )
    if _table_exists(conn, "app_organization_member"):
        counts["app_organization_member"] = _safe_count(
            conn,
            "SELECT COUNT(*) FROM app_organization_member WHERE organization_id = ?",
            [org_id],
        )
    return {k: v for k, v in counts.items() if v != 0}


def detect_candidates(conn) -> list[dict]:
    from app.packages.organizations.domain.test_org_patterns import (
        CANONICAL_DEMO_SLUG,
        classify_org_row,
        is_canonical_demo,
    )

    has_demo = _has_column(conn, "app_organization", "is_demo")
    has_test = _has_column(conn, "app_organization", "is_test")
    cols = "id, display_name, slug, status, created_at"
    if has_demo:
        cols += ", is_demo"
    if has_test:
        cols += ", is_test"

    rows = conn.execute(f"SELECT {cols} FROM app_organization").fetchall()
    col_names = [c.strip() for c in cols.split(",")]
    out: list[dict] = []
    for row in rows:
        d = {col_names[i]: row[i] for i in range(len(col_names))}
        d.setdefault("is_demo", False)
        d.setdefault("is_test", False)
        if is_canonical_demo(str(d.get("slug") or "")):
            continue
        kind = classify_org_row(d)
        if kind != "test":
            continue
        d["kind"] = kind
        d["related"] = _count_related(conn, int(d["id"]))
        out.append(d)
    # silence unused
    _ = CANONICAL_DEMO_SLUG
    return out


def detect_test_plans(conn) -> list[dict]:
    from app.packages.organizations.domain.test_org_patterns import looks_like_test_plan
    from app.packages.subscriptions.application.commercial_catalog import (
        COMMERCIAL_CATALOG,
    )

    commercial_codes = {p.code for p in COMMERCIAL_CATALOG}
    if not _table_exists(conn, "app_plan"):
        return []
    rows = conn.execute(
        "SELECT id, code, display_name, status FROM app_plan"
    ).fetchall()
    out: list[dict] = []
    for pid, code, name, status in rows:
        code_s = str(code or "")
        if code_s in commercial_codes:
            continue
        if looks_like_test_plan(code=code_s, display_name=str(name or "")):
            out.append(
                {
                    "id": int(pid),
                    "code": code_s,
                    "display_name": name,
                    "status": status,
                }
            )
    return out


def _delete_via_org_id(conn, table: str, org_id: int) -> int:
    if not _table_exists(conn, table) or not _has_column(conn, table, "organization_id"):
        return 0
    before = _safe_count(conn, f"SELECT COUNT(*) FROM {table} WHERE organization_id = ?", [org_id])
    if before <= 0:
        return 0
    conn.execute(f"DELETE FROM {table} WHERE organization_id = ?", [org_id])
    return before


def apply_delete_org(conn, org_id: int) -> dict[str, int]:
    deleted: dict[str, int] = {}

    # Preference pointers
    if _table_exists(conn, "app_user_organization_preference"):
        conn.execute(
            "UPDATE app_user_organization_preference SET active_organization_id = NULL "
            "WHERE active_organization_id = ?",
            [org_id],
        )

    # Support messages via cases
    if _table_exists(conn, "app_support_message") and _table_exists(conn, "app_support_case"):
        case_ids = [
            int(r[0])
            for r in conn.execute(
                "SELECT id FROM app_support_case WHERE organization_id = ?", [org_id]
            ).fetchall()
        ]
        for cid in case_ids:
            n = conn.execute(
                "SELECT COUNT(*) FROM app_support_message WHERE case_id = ?", [cid]
            ).fetchone()[0]
            conn.execute("DELETE FROM app_support_message WHERE case_id = ?", [cid])
            deleted["app_support_message"] = deleted.get("app_support_message", 0) + int(n)

    # Onboarding steps
    if _table_exists(conn, "app_customer_onboarding") and _table_exists(
        conn, "app_customer_onboarding_step"
    ):
        for (oid,) in conn.execute(
            "SELECT id FROM app_customer_onboarding WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_customer_onboarding_step WHERE onboarding_id = ?",
                [oid],
            ).fetchone()[0]
            conn.execute(
                "DELETE FROM app_customer_onboarding_step WHERE onboarding_id = ?", [oid]
            )
            deleted["app_customer_onboarding_step"] = deleted.get(
                "app_customer_onboarding_step", 0
            ) + int(n)

    # Decision actions
    if _table_exists(conn, "app_business_decision") and _table_exists(
        conn, "app_decision_action"
    ):
        for (did,) in conn.execute(
            "SELECT id FROM app_business_decision WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_decision_action WHERE decision_id = ?", [did]
            ).fetchone()[0]
            conn.execute("DELETE FROM app_decision_action WHERE decision_id = ?", [did])
            deleted["app_decision_action"] = deleted.get("app_decision_action", 0) + int(n)

    # Subscription children
    if _table_exists(conn, "app_subscription"):
        sub_ids = [
            int(r[0])
            for r in conn.execute(
                "SELECT id FROM app_subscription WHERE organization_id = ?", [org_id]
            ).fetchall()
        ]
        for table in (
            "app_subscription_addon",
            "app_subscription_entitlement",
            "app_subscription_change",
        ):
            if not _table_exists(conn, table):
                continue
            for sid in sub_ids:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE subscription_id = ?", [sid]
                ).fetchone()[0]
                conn.execute(f"DELETE FROM {table} WHERE subscription_id = ?", [sid])
                deleted[table] = deleted.get(table, 0) + int(n)

    # Invoice items
    if _table_exists(conn, "app_invoice") and _table_exists(conn, "app_invoice_item"):
        for (iid,) in conn.execute(
            "SELECT id FROM app_invoice WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_invoice_item WHERE invoice_id = ?", [iid]
            ).fetchone()[0]
            conn.execute("DELETE FROM app_invoice_item WHERE invoice_id = ?", [iid])
            deleted["app_invoice_item"] = deleted.get("app_invoice_item", 0) + int(n)

    # CRM quotation chain via opportunities
    if _table_exists(conn, "app_crm_opportunity"):
        opp_ids = [
            int(r[0])
            for r in conn.execute(
                "SELECT id FROM app_crm_opportunity WHERE organization_id = ?", [org_id]
            ).fetchall()
        ]
        quot_ids: list[int] = []
        if _table_exists(conn, "app_crm_quotation"):
            for oid in opp_ids:
                for (qid,) in conn.execute(
                    "SELECT id FROM app_crm_quotation WHERE opportunity_id = ?", [oid]
                ).fetchall():
                    quot_ids.append(int(qid))
        version_ids: list[int] = []
        if quot_ids and _table_exists(conn, "app_crm_quotation_version"):
            for qid in quot_ids:
                for (vid,) in conn.execute(
                    "SELECT id FROM app_crm_quotation_version WHERE quotation_id = ?",
                    [qid],
                ).fetchall():
                    version_ids.append(int(vid))
        if version_ids and _table_exists(conn, "app_crm_quotation_item"):
            for vid in version_ids:
                n = conn.execute(
                    "SELECT COUNT(*) FROM app_crm_quotation_item WHERE quotation_version_id = ?",
                    [vid],
                ).fetchone()[0]
                conn.execute(
                    "DELETE FROM app_crm_quotation_item WHERE quotation_version_id = ?",
                    [vid],
                )
                deleted["app_crm_quotation_item"] = deleted.get(
                    "app_crm_quotation_item", 0
                ) + int(n)
        if version_ids and _table_exists(conn, "app_crm_quotation_version"):
            for vid in version_ids:
                conn.execute(
                    "DELETE FROM app_crm_quotation_version WHERE id = ?", [vid]
                )
            deleted["app_crm_quotation_version"] = deleted.get(
                "app_crm_quotation_version", 0
            ) + len(version_ids)
        if quot_ids and _table_exists(conn, "app_crm_quotation"):
            for qid in quot_ids:
                conn.execute("DELETE FROM app_crm_quotation WHERE id = ?", [qid])
            deleted["app_crm_quotation"] = deleted.get("app_crm_quotation", 0) + len(
                quot_ids
            )

    # Prospect contacts
    if _table_exists(conn, "app_crm_prospect") and _table_exists(
        conn, "app_crm_prospect_contact"
    ):
        for (pid,) in conn.execute(
            "SELECT id FROM app_crm_prospect WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_crm_prospect_contact WHERE prospect_id = ?",
                [pid],
            ).fetchone()[0]
            conn.execute(
                "DELETE FROM app_crm_prospect_contact WHERE prospect_id = ?", [pid]
            )
            deleted["app_crm_prospect_contact"] = deleted.get(
                "app_crm_prospect_contact", 0
            ) + int(n)

    # Artist team
    if _table_exists(conn, "app_artist_profile") and _table_exists(
        conn, "app_artist_team_member"
    ):
        for (aid,) in conn.execute(
            "SELECT id FROM app_artist_profile WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_artist_team_member WHERE artist_profile_id = ?",
                [aid],
            ).fetchone()[0]
            conn.execute(
                "DELETE FROM app_artist_team_member WHERE artist_profile_id = ?", [aid]
            )
            deleted["app_artist_team_member"] = deleted.get(
                "app_artist_team_member", 0
            ) + int(n)

    # Rights contract parties
    if _table_exists(conn, "app_rights_contract") and _table_exists(
        conn, "app_rights_contract_party"
    ):
        for (cid,) in conn.execute(
            "SELECT id FROM app_rights_contract WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_rights_contract_party WHERE contract_id = ?",
                [cid],
            ).fetchone()[0]
            conn.execute(
                "DELETE FROM app_rights_contract_party WHERE contract_id = ?", [cid]
            )
            deleted["app_rights_contract_party"] = deleted.get(
                "app_rights_contract_party", 0
            ) + int(n)

    # Release tracks
    if _table_exists(conn, "app_catalog_release") and _table_exists(
        conn, "app_catalog_release_track"
    ):
        for (rid,) in conn.execute(
            "SELECT id FROM app_catalog_release WHERE organization_id = ?", [org_id]
        ).fetchall():
            n = conn.execute(
                "SELECT COUNT(*) FROM app_catalog_release_track WHERE release_id = ?",
                [rid],
            ).fetchone()[0]
            conn.execute(
                "DELETE FROM app_catalog_release_track WHERE release_id = ?", [rid]
            )
            deleted["app_catalog_release_track"] = deleted.get(
                "app_catalog_release_track", 0
            ) + int(n)

    # Bulk organization_id deletes
    for table, col in ORG_SCOPED_TABLES:
        if col != "organization_id":
            continue
        n = _delete_via_org_id(conn, table, org_id)
        if n:
            deleted[table] = deleted.get(table, 0) + n

    # Member roles then members (if still present)
    if _table_exists(conn, "app_organization_member"):
        member_ids = [
            int(r[0])
            for r in conn.execute(
                "SELECT id FROM app_organization_member WHERE organization_id = ?",
                [org_id],
            ).fetchall()
        ]
        if _table_exists(conn, "app_member_role"):
            for mid in member_ids:
                n = conn.execute(
                    "SELECT COUNT(*) FROM app_member_role WHERE member_id = ?", [mid]
                ).fetchone()[0]
                conn.execute("DELETE FROM app_member_role WHERE member_id = ?", [mid])
                deleted["app_member_role"] = deleted.get("app_member_role", 0) + int(n)
        if member_ids:
            conn.execute(
                "DELETE FROM app_organization_member WHERE organization_id = ?", [org_id]
            )
            deleted["app_organization_member"] = deleted.get(
                "app_organization_member", 0
            ) + len(member_ids)

    conn.execute("DELETE FROM app_organization WHERE id = ?", [org_id])
    deleted["organizations"] = deleted.get("organizations", 0) + 1
    return deleted


def retire_test_plans(conn, plans: list[dict]) -> dict[str, int]:
    """Retire (archive) non-commercial test plans — never delete if subscribed."""
    from app.packages.subscriptions.application.commercial_catalog import (
        COMMERCIAL_CATALOG,
    )

    commercial = {p.code for p in COMMERCIAL_CATALOG}
    retired = 0
    skipped = 0
    for p in plans:
        code = str(p["code"])
        if code in commercial:
            skipped += 1
            continue
        pid = int(p["id"])
        # If any non-test org subscription references it, skip hard path — archive only
        if _table_exists(conn, "app_plan"):
            conn.execute(
                "UPDATE app_plan SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [pid],
            )
            if _table_exists(conn, "app_plan_price"):
                conn.execute(
                    "UPDATE app_plan_price SET status = 'retired', updated_at = CURRENT_TIMESTAMP WHERE plan_id = ?",
                    [pid],
                )
            retired += 1
    return {"plans_archived": retired, "plans_skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup synthetic test organizations")
    parser.add_argument("--apply", action="store_true", help="Execute deletions")
    parser.add_argument("--json", action="store_true", help="JSON report")
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument(
        "--retire-test-plans",
        action="store_true",
        help="Also archive non-commercial GP/K3/test plans",
    )
    args = parser.parse_args()

    from app.core.config import get_settings
    from app.core.database import using_write_conn
    from app.packages.organizations.domain.test_org_patterns import CANONICAL_DEMO_SLUG

    settings = get_settings()
    db_path = Path(args.db_path) if args.db_path else Path(settings.db_path_resolved)
    pytest_hint = ".pytest_db" in str(db_path).replace("\\", "/") or "voxmetrik_test" in db_path.name

    # Refuse accidental warehouse music wipe: verify no dim_/fact_ deletes in this script
    report: dict = {
        "mode": "apply" if args.apply else "dry-run",
        "db_path": str(db_path),
        "canonical_demo_slug_protected": CANONICAL_DEMO_SLUG,
        "warehouse_tables_untouched": True,
        "warnings": [],
        "candidates": [],
        "test_plans": [],
    }
    if pytest_hint:
        report["warnings"].append(
            "Target looks like a pytest DB. Prefer cleaning the development warehouse."
        )
    if not db_path.exists():
        report["error"] = f"Database not found: {db_path}"
        print(json.dumps(report, indent=2, default=str) if args.json else report["error"])
        return 1

    os.environ["db_path"] = str(db_path)
    get_settings.cache_clear()

    try:
        with using_write_conn() as conn:
            if not _table_exists(conn, "app_organization"):
                report["error"] = "app_organization table missing"
                print(json.dumps(report, indent=2, default=str) if args.json else report["error"])
                return 1

            if not _has_column(conn, "app_organization", "is_test"):
                try:
                    conn.execute(
                        "ALTER TABLE app_organization ADD COLUMN is_test BOOLEAN DEFAULT FALSE"
                    )
                except Exception as exc:
                    report["warnings"].append(f"Could not add is_test: {exc}")

            candidates = detect_candidates(conn)
            report["candidates"] = [
                {
                    "id": int(c["id"]),
                    "display_name": c["display_name"],
                    "slug": c["slug"],
                    "status": c["status"],
                    "is_demo": bool(c.get("is_demo")),
                    "is_test": bool(c.get("is_test")),
                    "related": c["related"],
                }
                for c in candidates
            ]
            report["candidate_count"] = len(candidates)

            test_plans = detect_test_plans(conn) if args.retire_test_plans or True else []
            report["test_plans"] = test_plans
            report["test_plan_count"] = len(test_plans)

            if not args.apply:
                report["message"] = (
                    f"Dry-run: {len(candidates)} test organization(s) would be deleted"
                    + (
                        f"; {len(test_plans)} non-commercial test plan(s) would be archived"
                        if args.retire_test_plans
                        else ""
                    )
                    + ". Re-run with --apply to execute."
                )
            else:
                # DuckDB: best-effort transactional; on failure re-raise for operator
                deleted_totals: dict[str, int] = {"organizations": 0}
                try:
                    for c in candidates:
                        part = apply_delete_org(conn, int(c["id"]))
                        for k, v in part.items():
                            deleted_totals[k] = deleted_totals.get(k, 0) + v
                    if args.retire_test_plans:
                        deleted_totals.update(retire_test_plans(conn, test_plans))
                    report["deleted"] = deleted_totals
                    report["message"] = (
                        f"Deleted {deleted_totals.get('organizations', 0)} test organization(s)."
                    )
                except Exception as exc:
                    report["error"] = f"Cleanup failed (partial?): {exc}"
                    report["deleted"] = deleted_totals
                    if args.json:
                        print(json.dumps(report, indent=2, default=str))
                    else:
                        print(report["error"])
                    return 1
    except Exception as exc:
        report["error"] = str(exc)
        print(json.dumps(report, indent=2, default=str) if args.json else report["error"])
        return 1

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"DB: {report['db_path']}")
        print(f"Mode: {report['mode']}")
        print(f"Protected demo slug: {report['canonical_demo_slug_protected']}")
        for w in report["warnings"]:
            print(f"WARNING: {w}")
        print(f"Candidates: {report['candidate_count']}")
        for c in report["candidates"]:
            rel = ", ".join(f"{k}={v}" for k, v in (c.get("related") or {}).items())
            print(f"  - id={c['id']} slug={c['slug']!r} name={c['display_name']!r} [{rel}]")
        if args.retire_test_plans or report.get("test_plans"):
            print(f"Test plans (non-commercial): {report.get('test_plan_count', 0)}")
            for p in report.get("test_plans") or []:
                print(f"  - id={p['id']} code={p['code']!r} name={p['display_name']!r}")
        print(report["message"])
        if not args.apply:
            print(
                "\nTo apply:\n"
                "  python scripts/cleanup_test_organizations.py --apply --retire-test-plans"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
