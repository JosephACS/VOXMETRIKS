# -*- coding: utf-8 -*-
"""roles-permissions report must use display_name and return real rows."""

from __future__ import annotations

import duckdb

from app.core.database import using_write_conn
from app.packages.organizations.infrastructure.schema import ensure_organization_tables
from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
from app.packages.simple_reports.queries import _roles_permissions, run_report


def test_roles_permissions_returns_real_display_names():
    """Prove the query works with display_name (not swallowed empty by _safe_query)."""
    with using_write_conn() as conn:
        ensure_platform_rbac_tables(conn)
        ensure_organization_tables(conn)

        # Direct SQL with the fixed column — must succeed and yield rows.
        direct = conn.execute(
            """
            SELECT r.code AS role_code, COALESCE(r.display_name, r.code) AS role_name,
                   p.code AS permission_code, 'platform' AS scope
            FROM app_platform_role r
            JOIN app_platform_role_permission rp ON rp.role_id = r.id
            JOIN app_platform_permission p ON p.id = rp.permission_id
            ORDER BY r.code, p.code
            LIMIT 5
            """
        ).fetchall()
        assert len(direct) >= 1
        assert direct[0][1]  # role_name present

        items = _roles_permissions(conn)
        assert len(items) >= 1, "roles-permissions must not hide schema errors via empty _safe_query"
        platform_rows = [i for i in items if i.get("scope") == "platform"]
        assert platform_rows, items[:3]
        for row in platform_rows[:5]:
            assert row.get("role_code")
            assert row.get("role_name")
            assert row.get("permission_code")
            # display_name seed uses human labels (e.g. "Platform Admin"), not only code
            assert isinstance(row["role_name"], str) and len(row["role_name"]) > 0

        # Broken column name must not be what we ship — sanity: r.name would fail here.
        try:
            conn.execute(
                "SELECT COALESCE(r.name, r.code) FROM app_platform_role r LIMIT 1"
            ).fetchone()
            named_ok = True
        except Exception:
            named_ok = False
        assert named_ok is False, "schema still exposes r.name — unexpected"

        items_page, total = run_report(conn, "roles-permissions", limit=50, offset=0)
        assert total >= 1
        assert any(i.get("scope") == "platform" for i in items_page)


def test_roles_permissions_memory_schema_display_name_only():
    conn = duckdb.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE app_platform_role (
            id INTEGER, code VARCHAR, display_name VARCHAR
        );
        CREATE TABLE app_platform_permission (id INTEGER, code VARCHAR);
        CREATE TABLE app_platform_role_permission (role_id INTEGER, permission_id INTEGER);
        """
    )
    conn.execute("INSERT INTO app_platform_role VALUES (1, 'platform_admin', 'Platform Admin')")
    conn.execute("INSERT INTO app_platform_permission VALUES (10, 'ops.view')")
    conn.execute("INSERT INTO app_platform_role_permission VALUES (1, 10)")

    items = _roles_permissions(conn)
    assert len(items) == 1
    assert items[0]["role_code"] == "platform_admin"
    assert items[0]["role_name"] == "Platform Admin"
    assert items[0]["permission_code"] == "ops.view"
    conn.close()
