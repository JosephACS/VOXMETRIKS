"""Test R3: Reporting API — Spec 024."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now


@pytest.fixture(scope="module")
def report_admin(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200
    token = resp.json()["token"]
    user_id = resp.json().get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json().get("id") or (me.json().get("user") or {}).get("id")
    headers = {"Authorization": f"Bearer {token}"}
    org_id = 9241

    with using_write_conn() as conn:
        now = utc_now()
        from app.packages.organizations.infrastructure.schema import ensure_organization_role_catalogs

        ensure_organization_role_catalogs(conn)
        if not conn.execute("SELECT id FROM app_organization WHERE id = ?", [org_id]).fetchone():
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (?, 'Reporting API Org', 'reporting-api-org', 'label', 'US', 'UTC',
                        'USD', 'active', ?, ?, ?)
                """,
                [org_id, int(user_id), now, now],
            )
        m_row = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
            [org_id, int(user_id)],
        ).fetchone()
        if not m_row:
            mid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?, ?)
                """,
                [mid, org_id, int(user_id), int(user_id), now, now],
            )
            member_id = mid
        else:
            member_id = int(m_row[0])
        rid = conn.execute("SELECT id FROM app_business_role WHERE code = 'owner'").fetchone()[0]
        if not conn.execute(
            "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
            [member_id, int(rid)],
        ).fetchone():
            mrid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_member_role
                    (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                [mrid, member_id, int(rid), int(user_id), now],
            )

    return {"org_headers": {**headers, "X-Organization-Id": str(org_id)}, "org_id": org_id}


def test_report_generation_approve_publish_export(client: TestClient, report_admin):
    h = report_admin["org_headers"]
    d = client.post(
        "/api/v1/reports/definitions",
        headers=h,
        json={"code": "api-exec", "title": "API Executive"},
    )
    assert d.status_code == 201, d.text
    def_id = d.json()["id"]

    g = client.post(
        "/api/v1/reports/generations",
        headers=h,
        json={"definition_id": def_id, "period_start": "2026-01-01", "period_end": "2026-01-31"},
    )
    assert g.status_code == 201, g.text
    gen_id = g.json()["id"]

    gen = client.post(f"/api/v1/reports/generations/{gen_id}/generate", headers=h)
    assert gen.status_code == 200, gen.text
    body = gen.json()
    report_id = body["executive_report"]["id"]
    assert body["generation"]["status"] == "ready"

    ap = client.post(f"/api/v1/reports/executive/{report_id}/approve", headers=h, json={})
    assert ap.status_code == 200, ap.text
    assert ap.json()["status"] == "approved"

    pub = client.post(f"/api/v1/reports/executive/{report_id}/publish", headers=h)
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"

    exp = client.get(f"/api/v1/reports/executive/{report_id}/export", headers=h)
    assert exp.status_code == 200
    assert "text/csv" in exp.headers.get("content-type", "")

    dec = client.post(
        "/api/v1/business-decisions",
        headers=h,
        json={
            "title": "Expand market",
            "proposal": "Enter LATAM",
            "executive_report_id": report_id,
        },
    )
    assert dec.status_code == 201, dec.text
    did = dec.json()["id"]
    assert client.post(f"/api/v1/business-decisions/{did}/approve", headers=h).status_code == 200
    act = client.post(
        f"/api/v1/business-decisions/{did}/actions",
        headers=h,
        json={"title": "Draft plan"},
    )
    assert act.status_code == 201
    fu = client.post(
        f"/api/v1/business-decisions/{did}/follow-ups",
        headers=h,
        json={"note": "Board reviewed"},
    )
    assert fu.status_code == 201
    assert client.post(f"/api/v1/business-decisions/{did}/complete", headers=h).status_code == 200

    canceled = client.post(
        "/api/v1/business-decisions",
        headers=h,
        json={"title": "Cancel proposal", "proposal": "Do not proceed"},
    )
    assert canceled.status_code == 201
    canceled_id = canceled.json()["id"]
    cancel = client.post(
        f"/api/v1/business-decisions/{canceled_id}/cancel",
        headers=h,
        json={"reason": "Insufficient evidence"},
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "canceled"


def test_missing_org_header(client: TestClient, report_admin):
    r = client.get(
        "/api/v1/reports/executive",
        headers={"Authorization": report_admin["org_headers"]["Authorization"]},
    )
    assert r.status_code == 400
