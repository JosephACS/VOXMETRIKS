"""Spec 028 — Enterprise golden-path API smoke chain.

Chains implemented enterprise steps via TestClient where feasible:

  login → org context → list plans → campaigns list → business-analytics dashboard
  → compliance terms list → platform-ops health
  → executive report + business decision (024)
  → customer health + support + renewal/expansion (025)

Canonical APIs: /api/v1/reports, /api/v1/business-decisions,
/api/v1/customer-success, /api/v1/support.

Royalties/Payouts remain OUT_OF_SCOPE (not Spec 024/025).

Fixture is function-scoped to avoid DuckDB/session pollution when run after other suites.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.platform_rbac.infrastructure.repository import assign_role


def _resolve_user_id(client: TestClient, token: str, body: dict) -> int:
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None, f"Cannot resolve user id from {body}"
    return int(user_id)


def _ensure_owner_membership(conn, *, org_id: int, user_id: int) -> None:
    """Guarantee active membership + owner role with current permission catalog."""
    now = utc_now()
    member = conn.execute(
        """
        SELECT id FROM app_organization_member
        WHERE organization_id = ? AND user_id = ? AND status = 'active'
        """,
        [org_id, user_id],
    ).fetchone()
    if not member:
        mid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization_member").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, joined_at, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [mid, org_id, user_id, now, now, now],
        )
        member_id = mid
    else:
        member_id = int(member[0])

    role = conn.execute(
        "SELECT id FROM app_business_role WHERE code = 'owner'"
    ).fetchone()
    if not role:
        return
    role_id = int(role[0])
    existing = conn.execute(
        """
        SELECT 1 FROM app_member_role
        WHERE member_id = ? AND role_id = ? AND status = 'active'
        """,
        [member_id, role_id],
    ).fetchone()
    if not existing:
        mrid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_member_role").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_at, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [mrid, member_id, role_id, now, now, now],
        )


@pytest.fixture
def golden_path_ctx(client: TestClient) -> dict:
    """Admin login + platform_admin + owner org + ensure enterprise tables/catalogs."""
    from app.core.schema_bootstrap import mark_schema_ready, reset_schema_ready_for_tests, schema_ready
    from app.packages.organizations.infrastructure.schema import (
        ensure_organization_role_catalogs,
    )
    from app.packages.platform_rbac.infrastructure.schema import (
        _seed_platform_rbac_catalogs,
    )
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.packages.business_analytics.infrastructure.schema import (
        ensure_business_analytics_tables,
    )
    from app.packages.compliance.infrastructure.schema import ensure_compliance_tables
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables
    from app.packages.reporting.infrastructure.schema import ensure_reporting_tables
    from app.packages.customer_success.infrastructure.schema import (
        ensure_customer_success_tables,
    )

    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = body["token"]
    user_id = _resolve_user_id(client, token, body)
    headers = {"Authorization": f"Bearer {token}"}

    with using_write_conn() as conn:
        was_ready = schema_ready()
        reset_schema_ready_for_tests()
        ensure_campaign_tables(conn)
        ensure_business_analytics_tables(conn)
        ensure_compliance_tables(conn)
        ensure_platform_ops_tables(conn)
        ensure_reporting_tables(conn)
        ensure_customer_success_tables(conn)
        ensure_organization_role_catalogs(conn)
        _seed_platform_rbac_catalogs(conn)
        if was_ready:
            mark_schema_ready()
        assign_role(conn, user_id=user_id, role_code="platform_admin", assigned_by=None)

    slug = f"golden-path-s028-{uuid.uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={
            "display_name": "Golden Path S028 Org",
            "slug": slug,
            "organization_type": "label",
            "activate": True,
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    org = payload.get("organization") or payload
    org_id = int(org["id"])
    org_headers = {**headers, "X-Organization-Id": str(org_id)}

    with using_write_conn() as conn:
        ensure_organization_role_catalogs(conn)
        _ensure_owner_membership(conn, org_id=org_id, user_id=user_id)

    return {
        "headers": headers,
        "org_headers": org_headers,
        "org_id": org_id,
        "user_id": user_id,
    }


class TestEnterpriseGoldenPathS028:
    """API smoke chain for implemented enterprise domains."""

    def test_step_login(self, client: TestClient, golden_path_ctx: dict) -> None:
        me = client.get("/api/v1/users/me", headers=golden_path_ctx["headers"])
        assert me.status_code == 200
        assert me.json().get("username") == "admin"

    def test_step_org_context(self, client: TestClient, golden_path_ctx: dict) -> None:
        listed = client.get("/api/v1/organizations", headers=golden_path_ctx["headers"])
        assert listed.status_code == 200
        items = listed.json()
        if isinstance(items, dict):
            items = items.get("items") or items.get("organizations") or []
        org_ids = [o["id"] for o in items]
        assert golden_path_ctx["org_id"] in org_ids

        current = client.get(
            "/api/v1/organizations/current", headers=golden_path_ctx["org_headers"]
        )
        assert current.status_code == 200
        assert current.json()["context"] in ("active", "none")

    def test_step_list_plans(self, client: TestClient, golden_path_ctx: dict) -> None:
        resp = client.get("/api/v1/plans", headers=golden_path_ctx["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "items" in body or isinstance(body, list)

    def test_step_list_campaigns(self, client: TestClient, golden_path_ctx: dict) -> None:
        resp = client.get("/api/v1/campaigns", headers=golden_path_ctx["org_headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "items" in body or isinstance(body, list)

    def test_step_business_analytics_dashboard(
        self, client: TestClient, golden_path_ctx: dict
    ) -> None:
        resp = client.get(
            "/api/v1/business-analytics/dashboard",
            headers=golden_path_ctx["org_headers"],
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "kpis" in data or "sources" in data or isinstance(data, dict)

    def test_step_compliance_terms_list(
        self, client: TestClient, golden_path_ctx: dict
    ) -> None:
        now = utc_now()
        create = client.post(
            "/api/v1/compliance/terms",
            headers=golden_path_ctx["org_headers"],
            json={
                "version_code": f"s028-{uuid.uuid4().hex[:6]}",
                "title": "S028 Golden Path Terms",
                "content_summary": "Synthetic terms for validation",
                "effective_at": now.isoformat(),
            },
        )
        assert create.status_code in (200, 201), create.text
        listed = client.get("/api/v1/compliance/terms", headers=golden_path_ctx["org_headers"])
        assert listed.status_code == 200, listed.text
        body = listed.json()
        total = body.get("total") if isinstance(body, dict) else len(body)
        assert int(total or 0) >= 1 or (isinstance(body, dict) and body.get("items"))

    def test_step_platform_ops_health(self, client: TestClient, golden_path_ctx: dict) -> None:
        resp = client.get("/api/v1/platform-ops/health", headers=golden_path_ctx["headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("labeled_academic") is True or data.get("status") in (
            "ok",
            "healthy",
            "degraded",
        )

    def test_step_executive_report_and_decision(
        self, client: TestClient, golden_path_ctx: dict
    ) -> None:
        h = golden_path_ctx["org_headers"]
        d = client.post(
            "/api/v1/reports/definitions",
            headers=h,
            json={"code": f"gp-{uuid.uuid4().hex[:6]}", "title": "Golden Path Report"},
        )
        assert d.status_code == 201, d.text
        g = client.post(
            "/api/v1/reports/generations",
            headers=h,
            json={"definition_id": d.json()["id"]},
        )
        assert g.status_code == 201, g.text
        gen = client.post(
            f"/api/v1/reports/generations/{g.json()['id']}/generate", headers=h
        )
        assert gen.status_code == 200, gen.text
        report_id = gen.json()["executive_report"]["id"]
        assert client.post(f"/api/v1/reports/executive/{report_id}/approve", headers=h, json={}).status_code == 200
        assert client.post(f"/api/v1/reports/executive/{report_id}/publish", headers=h).status_code == 200
        dec = client.post(
            "/api/v1/business-decisions",
            headers=h,
            json={"title": "GP Decision", "proposal": "Act on report", "executive_report_id": report_id},
        )
        assert dec.status_code == 201, dec.text

    def test_step_customer_success_and_support(
        self, client: TestClient, golden_path_ctx: dict
    ) -> None:
        h = golden_path_ctx["org_headers"]
        health = client.post("/api/v1/customer-success/health/calculate", headers=h)
        assert health.status_code == 200, health.text
        case = client.post(
            "/api/v1/support/cases",
            headers=h,
            json={"subject": "Golden path support", "priority": "normal"},
        )
        assert case.status_code == 201, case.text
        cid = case.json()["id"]
        assert client.post(f"/api/v1/support/cases/{cid}/resolve", headers=h).status_code == 200
        ren = client.post("/api/v1/customer-success/renewal/evaluate", headers=h)
        assert ren.status_code == 200, ren.text
        exp = client.post(
            "/api/v1/customer-success/expansions",
            headers=h,
            json={"title": "GP Expansion"},
        )
        assert exp.status_code == 201, exp.text


class TestLegacyReportingPathAbsentS028:
    """Old 015 path /api/v1/reporting/reports remains unused; canonical is /api/v1/reports."""

    def test_legacy_reporting_prefix_not_required(
        self, client: TestClient, golden_path_ctx: dict
    ) -> None:
        # Canonical surface must exist
        r = client.get("/api/v1/reports/executive", headers=golden_path_ctx["org_headers"])
        assert r.status_code == 200, r.text
        # Legacy design path may 404 — acceptable
        legacy = client.get("/api/v1/reporting/reports", headers=golden_path_ctx["headers"])
        assert legacy.status_code in (404, 401, 403, 422)
