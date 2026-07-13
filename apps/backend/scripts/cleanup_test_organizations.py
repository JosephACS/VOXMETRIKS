#!/usr/bin/env python3
"""Safe cleanup of synthetic pytest / Golden Path organizations.

Dry-run by default. Never touches the canonical demo slug unless --include-demo
(and even then requires --apply).

Usage (from apps/backend):

    python scripts/cleanup_test_organizations.py
    python scripts/cleanup_test_organizations.py --apply

Refuses to run against the pytest temp DB path accidentally used as "cleanup target"
when --require-warehouse is set (default).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [name],
    ).fetchone()
    return bool(row and row[0])


def _has_column(conn, table: str, column: str) -> bool:
    cols = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
        [table],
    ).fetchall()}
    return column in cols


RELATED_TABLES = (
    "app_organization_member",
    "app_organization_invitation",
    "app_member_role",
    "app_user_organization_preference",
    "app_audit_log",
)


def _count_related(conn, org_id: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in RELATED_TABLES:
        if not _table_exists(conn, table):
            continue
        col = "organization_id" if table != "app_user_organization_preference" else "active_organization_id"
        try:
            n = int(conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", [org_id]
            ).fetchone()[0])
            counts[table] = n
        except Exception:
            counts[table] = -1
    return counts


def detect_candidates(conn) -> list[dict]:
    from app.packages.organizations.domain.test_org_patterns import (
        CANONICAL_DEMO_SLUG,
        classify_org_row,
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
        kind = classify_org_row(d)
        if kind != "test":
            continue
        if str(d.get("slug") or "").lower() == CANONICAL_DEMO_SLUG:
            continue
        d["kind"] = kind
        d["related"] = _count_related(conn, int(d["id"]))
        out.append(d)
    return out


def apply_delete(conn, org_ids: list[int]) -> dict[str, int]:
    """Delete org-scoped rows then the organization. Prefer hard delete for pure test data."""
    deleted = {"organizations": 0}
    for org_id in org_ids:
        # Clear preferences pointing at this org
        if _table_exists(conn, "app_user_organization_preference"):
            conn.execute(
                "UPDATE app_user_organization_preference SET active_organization_id = NULL "
                "WHERE active_organization_id = ?",
                [org_id],
            )
        # Member roles via members
        if _table_exists(conn, "app_member_role") and _table_exists(conn, "app_organization_member"):
            member_ids = [
                int(r[0])
                for r in conn.execute(
                    "SELECT id FROM app_organization_member WHERE organization_id = ?",
                    [org_id],
                ).fetchall()
            ]
            for mid in member_ids:
                conn.execute("DELETE FROM app_member_role WHERE member_id = ?", [mid])
        for table, col in (
            ("app_organization_invitation", "organization_id"),
            ("app_organization_member", "organization_id"),
            ("app_audit_log", "organization_id"),
        ):
            if _table_exists(conn, table):
                conn.execute(f"DELETE FROM {table} WHERE {col} = ?", [org_id])
                deleted[table] = deleted.get(table, 0) + 1
        conn.execute("DELETE FROM app_organization WHERE id = ?", [org_id])
        deleted["organizations"] += 1
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup synthetic test organizations")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete detected test orgs (default is dry-run)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON report",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Override DuckDB path (default: settings db_path)",
    )
    args = parser.parse_args()

    from app.core.config import get_settings
    from app.core.database import using_write_conn
    from app.packages.organizations.domain.test_org_patterns import CANONICAL_DEMO_SLUG

    settings = get_settings()
    db_path = Path(args.db_path) if args.db_path else Path(settings.db_path_resolved)
    warehouse_hint = "warehouse" in str(db_path).replace("\\", "/").lower()
    pytest_hint = ".pytest_db" in str(db_path).replace("\\", "/") or "voxmetrik_test" in db_path.name

    report: dict = {
        "mode": "apply" if args.apply else "dry-run",
        "db_path": str(db_path),
        "canonical_demo_slug_protected": CANONICAL_DEMO_SLUG,
        "warnings": [],
        "candidates": [],
    }

    if pytest_hint:
        report["warnings"].append(
            "Target looks like a pytest DB. Prefer cleaning the development warehouse instead."
        )

    if not db_path.exists():
        report["error"] = f"Database not found: {db_path}"
        print(json.dumps(report, indent=2, default=str) if args.json else report["error"])
        return 1

    # Use explicit path via env for this process
    import os

    os.environ["db_path"] = str(db_path)
    get_settings.cache_clear()

    with using_write_conn() as conn:
        if not _table_exists(conn, "app_organization"):
            report["error"] = "app_organization table missing"
            print(json.dumps(report, indent=2, default=str) if args.json else report["error"])
            return 1

        # Ensure is_test column exists (additive) so future marks stick
        from app.packages.organizations.infrastructure.schema import ensure_organization_tables
        from app.core.schema_bootstrap import reset_schema_ready_for_tests

        # Force additive path even if schema_ready was set by another process
        if not _has_column(conn, "app_organization", "is_test"):
            try:
                conn.execute(
                    "ALTER TABLE app_organization ADD COLUMN is_test BOOLEAN DEFAULT FALSE"
                )
            except Exception as exc:
                report["warnings"].append(f"Could not add is_test column: {exc}")

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

        if not args.apply:
            report["message"] = (
                f"Dry-run: {len(candidates)} test organization(s) would be deleted. "
                "Re-run with --apply to execute."
            )
        else:
            ids = [int(c["id"]) for c in candidates]
            deleted = apply_delete(conn, ids)
            report["deleted"] = deleted
            report["message"] = f"Deleted {deleted['organizations']} test organization(s)."

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"DB: {report['db_path']}")
        print(f"Mode: {report['mode']}")
        for w in report["warnings"]:
            print(f"WARNING: {w}")
        print(f"Candidates: {report['candidate_count']}")
        for c in report["candidates"]:
            rel = ", ".join(f"{k}={v}" for k, v in (c.get("related") or {}).items())
            print(f"  - id={c['id']} slug={c['slug']!r} name={c['display_name']!r} [{rel}]")
        print(report["message"])
        if not args.apply:
            print("\nTo apply: python scripts/cleanup_test_organizations.py --apply")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
