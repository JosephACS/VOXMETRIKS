#!/usr/bin/env python3
"""Read-only check of final demo warehouse state (academic closure).

Never prints passwords. Exit 0 when core checks pass (WARN allowed).

Usage (from apps/backend):

    python scripts/verify_final_demo_state.py
    python scripts/verify_final_demo_state.py --cleanup-dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_seed_constants():
    path = _BACKEND / "scripts" / "seed_integrated_demo.py"
    spec = importlib.util.spec_from_file_location("seed_integrated_demo", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.DEMO_USERS, mod.ORG_SLUG


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and int(row[0]) > 0)


def _check_catalogs() -> list[str]:
    warns: list[str] = []
    from app.packages.personal_subscriptions.application.catalog import PERSONAL_CATALOG
    from app.packages.subscriptions.application.commercial_catalog import (
        COMMERCIAL_CATALOG,
    )

    personal_monthly = {}
    for plan in PERSONAL_CATALOG:
        for price in plan.prices:
            if price.billing_period == "monthly":
                personal_monthly[plan.code] = price.amount
    if personal_monthly.get("premium_individual") != Decimal("4.99"):
        warns.append(
            "WARN personal premium_individual monthly expected 4.99 "
            f"got {personal_monthly.get('premium_individual')}"
        )
    else:
        print("OK personal_catalog premium_individual monthly=4.99")

    commercial_monthly = {
        plan.code: next(
            (p.amount for p in plan.prices if p.billing_period == "monthly"), None
        )
        for plan in COMMERCIAL_CATALOG
    }
    expected = {
        "starter": Decimal("49.00"),
        "professional": Decimal("99.00"),
        "business": Decimal("199.00"),
        "enterprise": Decimal("499.00"),
    }
    for code, amt in expected.items():
        got = commercial_monthly.get(code)
        if got != amt:
            warns.append(f"WARN commercial {code} monthly expected {amt} got {got}")
        else:
            print(f"OK commercial_catalog {code} monthly={amt}")
    return warns


def _pollution_query(conn) -> list[tuple]:
    if not _table_exists(conn, "app_organization"):
        return []
    return conn.execute(
        """
        SELECT id, display_name, slug FROM app_organization
        WHERE LOWER(COALESCE(display_name, '')) LIKE '%stagetest%'
           OR LOWER(COALESCE(display_name, '')) LIKE '%acme%'
           OR LOWER(COALESCE(display_name, '')) LIKE '%gp plan%'
           OR LOWER(COALESCE(display_name, '')) LIKE '%golden path%'
           OR LOWER(COALESCE(slug, '')) LIKE 'gp-%'
           OR LOWER(COALESCE(slug, '')) LIKE 'golden-path%'
           OR LOWER(COALESCE(slug, '')) = 'api-acme'
        """
    ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify final demo warehouse state")
    parser.add_argument(
        "--cleanup-dry-run",
        action="store_true",
        help="Print count (and names) of test-like orgs; never delete",
    )
    args = parser.parse_args()

    warns: list[str] = []
    core_ok = True

    demo_users, org_slug = _load_seed_constants()
    warns.extend(_check_catalogs())

    from app.core.config import get_settings

    settings = get_settings()
    media_root = Path(getattr(settings, "media_storage_root", None) or "data/media")
    if not media_root.is_absolute():
        media_root = (_BACKEND / media_root).resolve()
    if media_root.exists():
        print(f"OK media_root exists: {media_root}")
    else:
        msg = f"WARN media_root missing: {media_root}"
        print(msg)
        warns.append(msg)

    db_path = Path(settings.db_path_resolved)
    if not db_path.exists():
        print(f"FAIL warehouse DB missing: {db_path}")
        return 1
    print(f"OK warehouse open: {db_path}")

    from app.core.database import using_write_conn

    with using_write_conn() as conn:
        expected_users = [u for u, _ in demo_users]
        if not _table_exists(conn, "app_user"):
            print("MISSING app_user table")
            core_ok = False
        else:
            present = {
                r[0]
                for r in conn.execute(
                    "SELECT username FROM app_user WHERE username IN ("
                    + ",".join("?" for _ in expected_users)
                    + ")",
                    expected_users,
                ).fetchall()
            }
            missing = [u for u in expected_users if u not in present]
            if missing:
                print(f"MISSING DEMO_USERS: {missing}")
                warns.append(f"MISSING DEMO_USERS: {missing}")
            else:
                print(f"OK DEMO_USERS present count={len(present)}")

        if not _table_exists(conn, "app_organization"):
            print("MISSING app_organization table")
            core_ok = False
        else:
            row = conn.execute(
                "SELECT id, display_name FROM app_organization WHERE slug = ?",
                [org_slug],
            ).fetchone()
            if not row:
                print(f"MISSING org slug={org_slug}")
                core_ok = False
            else:
                print(f"OK org slug={org_slug} id={row[0]} name={row[1]}")

        if _table_exists(conn, "dim_track"):
            n = int(conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0])
            print(f"dim_track_count={n}")
            if n == 0:
                warns.append("WARN dim_track count is 0")
                print("WARN dim_track count is 0")
        else:
            print("MISSING dim_track table")
            core_ok = False

        pollution = _pollution_query(conn)
        print(f"test_like_orgs_count={len(pollution)}")
        if pollution:
            print(f"WARN test-like orgs found count={len(pollution)}")
            warns.append(f"WARN test-like orgs found count={len(pollution)}")
            if args.cleanup_dry_run:
                for oid, name, slug in pollution:
                    print(
                        f"  cleanup-dry-run would consider id={oid} "
                        f"slug={slug} name={name}"
                    )

    if core_ok:
        print("RESULT: PASS (core checks ok; warnings allowed)")
        return 0
    print("RESULT: FAIL (core org/warehouse checks)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
