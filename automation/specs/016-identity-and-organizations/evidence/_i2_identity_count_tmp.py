from pathlib import Path
import duckdb

ROOT = Path(r"C:\Users\Admin\Documents\Tarea\Proyectos\Ariosto\voxmetriks")
WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
OUT = ROOT / "automation" / "specs" / "016-identity-and-organizations" / "evidence" / "_i2_identity_after.txt"
lines = []

def log(msg=""):
    print(msg)
    lines.append(msg)

def count_or_na(conn, table):
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except Exception:
        return "TABLE_MISSING"

exit_code = 0
log(f"warehouse={WAREHOUSE}")
log(f"exists={WAREHOUSE.exists()}")
if not WAREHOUSE.exists():
    log("FAIL: warehouse missing")
    exit_code = 1
else:
    conn = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        users = count_or_na(conn, "app_user")
        sessions = count_or_na(conn, "app_session")
        codes = count_or_na(conn, "app_email_code")
        orgs = count_or_na(conn, "app_organization")
        members = count_or_na(conn, "app_organization_member")
        roles = count_or_na(conn, "app_business_role")
        perms = count_or_na(conn, "app_permission")
        rp = count_or_na(conn, "app_role_permission")
        mr = count_or_na(conn, "app_member_role")
        log("=== IDENTITY ===")
        log(f"  app_user: {users}")
        log(f"  app_session: {sessions}")
        log(f"  app_email_code: {codes}")
        log("=== ORGS ===")
        log(f"  app_organization: {orgs}")
        log(f"  app_organization_member: {members}")
        log("=== CATALOGS ===")
        log(f"  app_business_role: {roles}")
        log(f"  app_permission: {perms}")
        log(f"  app_role_permission: {rp}")
        log(f"  app_member_role: {mr}")
        ok_id = users == 5 and sessions == 243 and codes == 0
        ok_org = orgs == 0 and members == 0
        ok_cat = roles == 9 and perms == 15 and rp == 48
        log(f"EXPECT identity 5/243/0: {'PASS' if ok_id else 'FAIL'}")
        log(f"EXPECT orgs 0/0: {'PASS' if ok_org else 'FAIL'}")
        log(f"EXPECT catalogs 9/15/48: {'PASS' if ok_cat else 'FAIL'}")
        if ok_id and ok_org and ok_cat:
            log("PASS")
        else:
            log("FAIL")
            exit_code = 1
    finally:
        conn.close()

OUT.write_text("\n".join(lines) + f"\nEXIT={exit_code}\n", encoding="utf-8")
raise SystemExit(exit_code)
