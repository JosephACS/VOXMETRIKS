"""I1 warehouse apply: identity before/after + ensure_organization_tables on real warehouse."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Admin\Documents\Tarea\Proyectos\Ariosto\voxmetriks")
BACKEND = ROOT / "apps" / "backend"
WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
OUT = ROOT / "automation" / "specs" / "016-identity-and-organizations" / "evidence" / "_i1_warehouse_apply.txt"

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("SKIP_SYSTEM_BOOT", "1")
os.environ.setdefault("RUN_ETL_ON_BOOT", "never")
os.environ["db_path"] = str(WAREHOUSE)

lines: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    lines.append(msg)


def table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [name],
    ).fetchone()
    return row is not None


def count_or_na(conn, name: str) -> str:
    if not table_exists(conn, name):
        return "TABLE_MISSING"
    return str(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])


def snapshot(conn, label: str) -> None:
    log(f"=== {label} ===")
    for t in ("app_user", "app_session", "app_email_code"):
        log(f"  {t}: {count_or_na(conn, t)}")
    for t in ("app_organization", "app_organization_member"):
        log(f"  {t}: {count_or_na(conn, t)}")
    for t in ("app_business_role", "app_permission", "app_role_permission", "app_member_role"):
        log(f"  {t}: {count_or_na(conn, t)}")


def main() -> int:
    import duckdb

    log(f"warehouse={WAREHOUSE}")
    log(f"exists={WAREHOUSE.exists()}")
    if not WAREHOUSE.exists():
        log("FAIL: warehouse missing")
        OUT.write_text("\n".join(lines) + "\nEXIT=1\n", encoding="utf-8")
        return 1

    # Read-only snapshot first (safe if another process holds write)
    log("\n--- read-only before ---")
    try:
        rconn = duckdb.connect(str(WAREHOUSE), read_only=True)
        snapshot(rconn, "BEFORE (read-only)")
        rconn.close()
    except Exception as exc:
        log(f"FAIL read-only before: {type(exc).__name__}: {exc}")
        OUT.write_text("\n".join(lines) + "\nEXIT=1\n", encoding="utf-8")
        return 1

    # Write connection carefully for ensure
    log("\n--- write ensure_organization_tables ---")
    try:
        from app.core import schema_bootstrap

        schema_bootstrap._schema_ready = False
        log(f"schema_ready after reset: {schema_bootstrap.schema_ready()}")

        wconn = duckdb.connect(str(WAREHOUSE), read_only=False)
        try:
            from app.packages.organizations.infrastructure.schema import (
                ensure_organization_tables,
            )

            ensure_organization_tables(wconn)
            log("ensure_organization_tables: OK")
            snapshot(wconn, "AFTER (write conn)")
            org_count = count_or_na(wconn, "app_organization")
            log(f"\norg_seed_check: app_organization count={org_count} (expect 0 if no org seed)")
            if org_count not in ("TABLE_MISSING",) and int(org_count) == 0:
                log("CONFIRM: 0 organizations (catalogs only, no org seed)")
            elif org_count == "TABLE_MISSING":
                log("WARN: app_organization still missing after ensure")
            else:
                log(f"NOTE: app_organization has {org_count} rows (pre-existing or seeded)")
        finally:
            wconn.close()
    except Exception as exc:
        log(f"FAIL write/ensure: {type(exc).__name__}: {exc}")
        import traceback

        log(traceback.format_exc())
        OUT.write_text("\n".join(lines) + "\nEXIT=1\n", encoding="utf-8")
        return 1

    # Final read-only confirm
    log("\n--- read-only after ---")
    rconn = duckdb.connect(str(WAREHOUSE), read_only=True)
    snapshot(rconn, "AFTER (read-only)")
    roles = count_or_na(rconn, "app_business_role")
    perms = count_or_na(rconn, "app_permission")
    maps = count_or_na(rconn, "app_role_permission")
    orgs = count_or_na(rconn, "app_organization")
    rconn.close()
    log(f"\nsummary: roles={roles} permissions={perms} role_permissions={maps} orgs={orgs}")
    log("PASS")
    OUT.write_text("\n".join(lines) + "\nEXIT=0\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
