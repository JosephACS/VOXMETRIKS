"""Test Q5: Compliance security — Spec 026."""

from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.packages.compliance.application.use_cases import DataRequestUseCases
from app.packages.compliance.domain.errors import NotFoundError


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("compliance_sec") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.compliance.infrastructure.schema import ensure_compliance_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_compliance_tables(conn)

    now = utc_now()
    for oid, slug in [(90, "compliance-sec-a"), (91, "compliance-sec-b")]:
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, slug, organization_type, country_code, timezone,
                 default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
            """,
            [oid, f"Org {slug}", slug, now, now],
        )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_cross_tenant_dsr_blocked(db_conn):
    dr = DataRequestUseCases(db_conn).submit(
        requester_user_id=1, organization_id=90, request_type="access",
    )
    with pytest.raises(NotFoundError):
        DataRequestUseCases(db_conn).export_data(dr.id, 91, actor_user_id=1)


def test_viewer_cannot_manage_compliance(client: TestClient):
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    token = body["token"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json().get("id") or (me.json().get("user") or {}).get("id")
    assert user_id is not None
    user_id = int(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        if not conn.execute("SELECT 1 FROM app_organization WHERE slug = 'compliance-viewer-q5'").fetchone():
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (310, 'Compliance Viewer', 'compliance-viewer-q5', 'label',
                        'US', 'UTC', 'USD', 'active', ?, ?, ?)
                """,
                [int(user_id), now, now],
            )
        if not conn.execute(
            "SELECT 1 FROM app_organization_member WHERE organization_id = 310 AND user_id = ?",
            [int(user_id)],
        ).fetchone():
            mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 310, ?, 'active', ?, ?, ?)
                """,
                [mid, int(user_id), int(user_id), now, now],
            )
        viewer_role = conn.execute("SELECT id FROM app_business_role WHERE code = 'viewer'").fetchone()
        member = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 310 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if viewer_role and member:
            mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                [mrid, int(member[0]), int(viewer_role[0]), int(user_id), now],
            )

    headers["X-Organization-Id"] = "310"
    resp2 = client.post(
        "/api/v1/compliance/terms",
        headers=headers,
        json={
            "version_code": "blocked",
            "title": "Blocked",
            "content_summary": "Should fail",
            "effective_at": now.isoformat(),
        },
    )
    assert resp2.status_code == 403
