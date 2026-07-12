"""Test R5: Reporting security — Spec 024."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now


def _login(client: TestClient) -> tuple[str, int]:
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
    return token, int(user_id)


def _ensure_member(conn, *, org_id: int, user_id: int, role_code: str) -> None:
    from app.packages.organizations.infrastructure.schema import ensure_organization_role_catalogs

    ensure_organization_role_catalogs(conn)
    now = utc_now()
    if not conn.execute("SELECT id FROM app_organization WHERE id = ?", [org_id]).fetchone():
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, slug, organization_type, country_code, timezone,
                 default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?)
            """,
            [org_id, f"Org {org_id}", f"org-{org_id}", user_id, now, now],
        )
    m_row = conn.execute(
        "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
        [org_id, user_id],
    ).fetchone()
    if not m_row:
        mid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [mid, org_id, user_id, user_id, now, now],
        )
        member_id = mid
    else:
        member_id = int(m_row[0])
    rid = conn.execute("SELECT id FROM app_business_role WHERE code = ?", [role_code]).fetchone()
    assert rid, f"role {role_code} missing"
    # Replace active roles for this member (unique on member_id+role_id)
    conn.execute("DELETE FROM app_member_role WHERE member_id = ?", [member_id])
    mrid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
        VALUES (?, ?, ?, 'active', ?, ?)
        """,
        [mrid, member_id, int(rid[0]), user_id, now],
    )


@pytest.fixture
def sec_ctx(client: TestClient) -> dict:
    token, user_id = _login(client)
    org_a, org_b = 9250, 9251
    with using_write_conn() as conn:
        _ensure_member(conn, org_id=org_a, user_id=user_id, role_code="owner")
        _ensure_member(conn, org_id=org_b, user_id=user_id, role_code="viewer")
    return {
        "token": token,
        "user_id": user_id,
        "org_a": org_a,
        "org_b": org_b,
        "headers_a": {"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_a)},
        "headers_b": {"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_b)},
    }


def test_cross_tenant_cannot_see_other_org_report(client: TestClient, sec_ctx):
    h = sec_ctx["headers_a"]
    d = client.post(
        "/api/v1/reports/definitions",
        headers=h,
        json={"code": "sec-a", "title": "Sec A"},
    )
    assert d.status_code == 201
    g = client.post(
        "/api/v1/reports/generations",
        headers=h,
        json={"definition_id": d.json()["id"]},
    )
    assert g.status_code == 201
    gen = client.post(f"/api/v1/reports/generations/{g.json()['id']}/generate", headers=h)
    assert gen.status_code == 200
    report_id = gen.json()["executive_report"]["id"]

    # Org B viewer must not see Org A report
    r = client.get(f"/api/v1/reports/executive/{report_id}", headers=sec_ctx["headers_b"])
    assert r.status_code == 404


def test_viewer_cannot_generate(client: TestClient, sec_ctx):
    r = client.post(
        "/api/v1/reports/definitions",
        headers=sec_ctx["headers_b"],
        json={"code": "viewer-blocked", "title": "Nope"},
    )
    assert r.status_code == 403


def test_analyst_cannot_approve(client: TestClient, sec_ctx):
    token, user_id = sec_ctx["token"], sec_ctx["user_id"]
    org_c = 9252
    with using_write_conn() as conn:
        _ensure_member(conn, org_id=org_c, user_id=user_id, role_code="owner")
    h_owner = {"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_c)}
    d = client.post(
        "/api/v1/reports/definitions", headers=h_owner, json={"code": "an", "title": "An"}
    )
    g = client.post(
        "/api/v1/reports/generations", headers=h_owner, json={"definition_id": d.json()["id"]}
    )
    gen = client.post(f"/api/v1/reports/generations/{g.json()['id']}/generate", headers=h_owner)
    report_id = gen.json()["executive_report"]["id"]

    with using_write_conn() as conn:
        _ensure_member(conn, org_id=org_c, user_id=user_id, role_code="analyst")
    h_an = {"Authorization": f"Bearer {token}", "X-Organization-Id": str(org_c)}
    ap = client.post(f"/api/v1/reports/executive/{report_id}/approve", headers=h_an, json={})
    assert ap.status_code == 403
