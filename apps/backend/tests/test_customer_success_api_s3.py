"""Test S2/S3: Customer success & support API — Spec 025."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now


@pytest.fixture(scope="module")
def cs_admin(client: TestClient) -> dict:
    resp = client.post("/api/v1/users/login", json={"login": "admin", "password": "admin123", "remember": True})
    assert resp.status_code == 200
    token = resp.json()["token"]
    user_id = resp.json().get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json().get("id") or (me.json().get("user") or {}).get("id")
    headers = {"Authorization": f"Bearer {token}"}
    org_id = 9350
    with using_write_conn() as conn:
        from app.packages.organizations.infrastructure.schema import ensure_organization_role_catalogs
        ensure_organization_role_catalogs(conn)
        now = utc_now()
        if not conn.execute("SELECT id FROM app_organization WHERE id = ?", [org_id]).fetchone():
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (?, 'CS Org', 'cs-org-9350', 'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?)
                """,
                [org_id, int(user_id), now, now],
            )
        m = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
            [org_id, int(user_id)],
        ).fetchone()
        if not m:
            mid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                "INSERT INTO app_organization_member (id, organization_id, user_id, status, created_by, created_at, updated_at) VALUES (?, ?, ?, 'active', ?, ?, ?)",
                [mid, org_id, int(user_id), int(user_id), now, now],
            )
            member_id = mid
        else:
            member_id = int(m[0])
        conn.execute("DELETE FROM app_member_role WHERE member_id = ?", [member_id])
        rid = conn.execute("SELECT id FROM app_business_role WHERE code = 'owner'").fetchone()[0]
        mrid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0])
        conn.execute(
            "INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at) VALUES (?, ?, ?, 'active', ?, ?)",
            [mrid, member_id, int(rid), int(user_id), now],
        )
    return {"org_headers": {**headers, "X-Organization-Id": str(org_id)}, "user_id": int(user_id), "org_id": org_id}


def test_onboarding_health_risk_support_lifecycle(client: TestClient, cs_admin):
    h = cs_admin["org_headers"]

    ob = client.post("/api/v1/customer-success/onboarding", headers=h)
    assert ob.status_code == 201, ob.text
    oid = ob.json()["id"]
    steps = client.get(f"/api/v1/customer-success/onboarding/{oid}/steps", headers=h)
    assert steps.status_code == 200
    step_id = steps.json()[0]["id"]
    assert client.post(f"/api/v1/customer-success/onboarding/{oid}/steps/{step_id}/complete", headers=h).status_code == 200

    health = client.post("/api/v1/customer-success/health/calculate", headers=h)
    assert health.status_code == 200, health.text
    assert health.json()["score_state"] in (
        "healthy", "watch", "risk", "critical", "insufficient_data", "No disponible",
    )
    assert "not AI" in (health.json().get("limitations") or "").lower() or "rule-based" in (health.json().get("limitations") or "").lower()

    risk = client.post("/api/v1/customer-success/risks", headers=h, json={"title": "Churn risk", "severity": "high"})
    assert risk.status_code == 201
    rid = risk.json()["id"]
    iv = client.post("/api/v1/customer-success/interventions", headers=h, json={"title": "Call customer", "risk_id": rid})
    assert iv.status_code == 201
    assert client.post(f"/api/v1/customer-success/interventions/{iv.json()['id']}/complete", headers=h).status_code == 200

    ren = client.post("/api/v1/customer-success/renewal/evaluate", headers=h)
    assert ren.status_code == 200
    exp = client.post("/api/v1/customer-success/expansions", headers=h, json={"title": "Upsell seats", "estimated_value": 1000})
    assert exp.status_code == 201

    case = client.post("/api/v1/support/cases", headers=h, json={"subject": "Login issue", "priority": "high"})
    assert case.status_code == 201, case.text
    cid = case.json()["id"]
    assert client.post(f"/api/v1/support/cases/{cid}/triage", headers=h).status_code == 200
    assert client.post(f"/api/v1/support/cases/{cid}/assign", headers=h, json={"assignee_user_id": cs_admin["user_id"]}).status_code == 200
    assert client.post(f"/api/v1/support/cases/{cid}/messages", headers=h, json={"body": "Looking into it"}).status_code == 201
    note = client.post(f"/api/v1/support/cases/{cid}/internal-notes", headers=h, json={"body": "Internal only"})
    assert note.status_code == 201
    assert note.json()["is_internal"] is True

    pub = client.get(f"/api/v1/support/cases/{cid}/messages", headers=h)
    assert pub.status_code == 200
    assert all(not m["is_internal"] for m in pub.json())

    internal = client.get(f"/api/v1/support/cases/{cid}/messages?include_internal=true", headers=h)
    assert internal.status_code == 200
    assert any(m["is_internal"] for m in internal.json())

    assert client.post(f"/api/v1/support/cases/{cid}/escalate", headers=h).status_code == 200
    assert client.post(f"/api/v1/support/cases/{cid}/resolve", headers=h).status_code == 200
    assert client.post(f"/api/v1/support/cases/{cid}/close", headers=h).status_code == 200
    sat = client.post(f"/api/v1/support/cases/{cid}/satisfaction", headers=h, json={"score": 5, "comment": "Great"})
    assert sat.status_code == 201
    sla = client.get(f"/api/v1/support/cases/{cid}/sla-events", headers=h)
    assert sla.status_code == 200
    assert len(sla.json()) >= 1

    reopened = client.post(f"/api/v1/support/cases/{cid}/reopen", headers=h)
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["status"] == "reopened"
    assert client.post(f"/api/v1/support/cases/{cid}/triage", headers=h).status_code == 200
    # Closed/resolved cannot be assigned without reopen (already reopened+triaged here)
    bad_assign = client.post(
        f"/api/v1/support/cases/{cid}/assign",
        headers=h,
        json={"assignee_user_id": cs_admin["user_id"]},
    )
    assert bad_assign.status_code == 200
    closed_again = client.post(f"/api/v1/support/cases/{cid}/resolve", headers=h)
    assert closed_again.status_code == 200
    assert client.post(f"/api/v1/support/cases/{cid}/close", headers=h).status_code == 200
    blocked = client.post(
        f"/api/v1/support/cases/{cid}/assign",
        headers=h,
        json={"assignee_user_id": cs_admin["user_id"]},
    )
    assert blocked.status_code in (409, 422)


def test_cross_tenant_support_404(client: TestClient, cs_admin):
    h = cs_admin["org_headers"]
    case = client.post("/api/v1/support/cases", headers=h, json={"subject": "Tenant A"})
    cid = case.json()["id"]
    other = {**h, "X-Organization-Id": "999999"}
    r = client.get(f"/api/v1/support/cases/{cid}", headers=other)
    assert r.status_code in (403, 404)
