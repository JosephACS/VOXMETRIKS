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
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables

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
        ensure_crm_tables(conn)
        ensure_commercial_contract_tables(conn)
        ensure_subscription_tables(conn)
        ensure_billing_tables(conn)
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


class TestEnterpriseGoldenPathCommercialS028:
    """Full CRM → plan → subscription → invoice → dunning → recovery → MRR chain."""

    def test_full_commercial_golden_path(self, client: TestClient, golden_path_ctx: dict) -> None:
        h = golden_path_ctx["headers"]
        org_h = golden_path_ctx["org_headers"]
        org_id = golden_path_ctx["org_id"]
        user_id = golden_path_ctx["user_id"]
        suffix = uuid.uuid4().hex[:8]

        # ── CRM: prospect → opportunity → quotation → accept → contract ──
        pr = client.post(
            "/api/v1/crm/prospects",
            headers=h,
            json={"display_name": f"GP Prospect {suffix}", "company_name": f"GP Co {suffix}"},
        )
        assert pr.status_code == 201, pr.text
        prospect_id = pr.json()["id"]

        opp = client.post(
            "/api/v1/crm/opportunities",
            headers=h,
            json={"prospect_id": prospect_id, "name": f"GP Deal {suffix}", "currency": "USD"},
        )
        assert opp.status_code == 201, opp.text
        opportunity_id = opp.json()["id"]

        quot = client.post(
            "/api/v1/crm/quotations",
            headers=h,
            json={"opportunity_id": opportunity_id, "currency": "USD"},
        )
        assert quot.status_code == 201, quot.text
        quotation_id = quot.json()["id"]

        ver = client.post(
            f"/api/v1/crm/quotations/{quotation_id}/versions",
            headers=h,
            json={},
        )
        assert ver.status_code == 201, ver.text
        version_id = ver.json()["id"]

        item = client.post(
            f"/api/v1/crm/quotation-versions/{version_id}/items",
            headers=h,
            json={
                "description": "Enterprise plan",
                "quantity": "1",
                "unit_price": "99.00",
                "discount_pct": "0",
            },
        )
        assert item.status_code == 201, item.text

        sent = client.post(
            f"/api/v1/crm/quotation-versions/{version_id}/send",
            headers=h,
            json={},
        )
        assert sent.status_code == 200, sent.text

        accepted = client.post(
            f"/api/v1/crm/quotation-versions/{version_id}/accept",
            headers=h,
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["status"] == "accepted"

        contract = client.post(
            "/api/v1/crm/contracts",
            headers=h,
            json={
                "quotation_version_id": version_id,
                "opportunity_id": opportunity_id,
                "legal_name": f"GP Legal {suffix}",
                "organization_id": org_id,
                "signatory_user_id": user_id,
            },
        )
        assert contract.status_code == 201, contract.text
        contract_id = contract.json()["id"]

        submitted = client.post(
            f"/api/v1/crm/contracts/{contract_id}/submit",
            headers=h,
            json={},
        )
        assert submitted.status_code == 200, submitted.text

        approved = client.post(
            f"/api/v1/crm/contracts/{contract_id}/approve",
            headers=h,
            json={},
        )
        assert approved.status_code == 200, approved.text

        accepted_c = client.post(
            f"/api/v1/crm/contracts/{contract_id}/accept",
            headers=h,
            json={"acceptance_evidence": "golden_path_academic"},
        )
        assert accepted_c.status_code == 200, accepted_c.text

        # ── Conversion Path A: link_existing → confirm ──
        prep = client.post(
            "/api/v1/crm/conversions",
            headers=h,
            json={
                "opportunity_id": opportunity_id,
                "mode": "link_existing",
                "idempotency_key": f"gp-conv-{suffix}",
            },
        )
        assert prep.status_code == 201, prep.text
        conversion_id = prep.json()["conversion"]["id"]

        confirm = client.post(
            f"/api/v1/crm/conversions/{conversion_id}/confirm-link",
            headers=org_h,
            json={"organization_id": org_id},
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["status"] == "completed"
        assert confirm.json()["organization_id"] == org_id

        # ── Plan catalog + select plan → subscription (no auto invoice) ──
        plan = client.post(
            "/api/v1/plans",
            headers=h,
            json={
                "code": f"gp-plan-{suffix}",
                "display_name": f"GP Plan {suffix}",
                "trial_days_default": 0,
            },
        )
        assert plan.status_code == 201, plan.text
        plan_id = plan.json()["id"]
        act = client.post(f"/api/v1/plans/{plan_id}/activate", headers=h)
        assert act.status_code == 200, act.text

        price = client.post(
            f"/api/v1/plans/{plan_id}/prices",
            headers=h,
            json={"currency": "USD", "billing_period": "monthly", "amount": "99.00"},
        )
        assert price.status_code == 201, price.text
        price_id = price.json()["id"]

        # Wrong currency rejected
        bad_ccy = client.post(
            "/api/v1/subscriptions",
            headers=org_h,
            json={
                "organization_id": org_id,
                "plan_id": plan_id,
                "plan_price_id": price_id,
                "billing_currency": "EUR",
                "activation_source": "crm_conversion",
            },
        )
        assert bad_ccy.status_code in (400, 409, 422), bad_ccy.text

        sub = client.post(
            "/api/v1/subscriptions",
            headers=org_h,
            json={
                "organization_id": org_id,
                "plan_id": plan_id,
                "plan_price_id": price_id,
                "billing_currency": "USD",
                "activation_source": "crm_conversion",
            },
        )
        assert sub.status_code == 201, sub.text
        subscription_id = sub.json()["id"]
        assert sub.json()["status"] == "active"
        assert sub.json()["access_state"] == "full"

        # No duplicate subscription
        dup = client.post(
            "/api/v1/subscriptions",
            headers=org_h,
            json={
                "organization_id": org_id,
                "plan_id": plan_id,
                "plan_price_id": price_id,
                "billing_currency": "USD",
            },
        )
        assert dup.status_code in (400, 409, 422), dup.text

        # Cross-tenant: other org header rejected for this subscription list scope
        other_org = client.post(
            "/api/v1/organizations",
            headers=h,
            json={
                "display_name": f"Other Org {suffix}",
                "slug": f"other-org-{suffix}",
                "organization_type": "label",
                "activate": True,
            },
        )
        assert other_org.status_code == 201, other_org.text
        other_id = int((other_org.json().get("organization") or other_org.json())["id"])
        with using_write_conn() as conn:
            _ensure_owner_membership(conn, org_id=other_id, user_id=user_id)
        foreign = client.get(
            f"/api/v1/subscriptions/{subscription_id}",
            headers={**h, "X-Organization-Id": str(other_id)},
        )
        assert foreign.status_code in (403, 404), foreign.text

        # Permission denied without auth
        anon = client.get("/api/v1/subscriptions", headers={"X-Organization-Id": str(org_id)})
        assert anon.status_code in (401, 403)

        # ── Invoice → fail attempt → dunning → limited access ──
        profile = client.post(
            "/api/v1/billing/profile",
            headers=org_h,
            json={"default_currency": "USD", "legal_name": f"GP Billing {suffix}"},
        )
        if profile.status_code == 409:
            profile = client.get("/api/v1/billing/profile", headers=org_h)
        assert profile.status_code in (200, 201), profile.text
        profile_id = profile.json()["id"]

        inv = client.post(
            "/api/v1/billing/invoices",
            headers=org_h,
            json={
                "billing_profile_id": profile_id,
                "subscription_id": subscription_id,
                "notes": "GP invoice",
            },
        )
        assert inv.status_code == 201, inv.text
        invoice_id = inv.json()["id"]

        assert client.post(
            f"/api/v1/billing/invoices/{invoice_id}/items",
            headers=org_h,
            json={"description": "Monthly", "quantity": "1", "unit_price": "99.00"},
        ).status_code == 201

        issued = client.post(f"/api/v1/billing/invoices/{invoice_id}/issue", headers=org_h)
        assert issued.status_code == 200, issued.text

        attempt = client.post(
            "/api/v1/billing/payment-attempts",
            headers=org_h,
            json={
                "invoice_id": invoice_id,
                "provider_code": "academic_mock",
                "idempotency_key": f"gp-fail-{suffix}",
                "amount": "99.00",
                "currency": "USD",
            },
        )
        assert attempt.status_code == 201, attempt.text
        attempt_id = attempt.json()["id"]

        failed = client.post(
            f"/api/v1/billing/payment-attempts/{attempt_id}/fail",
            headers=org_h,
            json={"failure_reason": "mock_card_declined"},
        )
        assert failed.status_code == 200, failed.text

        dunning = client.get(
            f"/api/v1/billing/dunning/by-invoice/{invoice_id}",
            headers=org_h,
        )
        assert dunning.status_code == 200, dunning.text
        dun = dunning.json()
        assert dun is not None
        assert dun["status"] in ("grace", "limited")
        assert dun["retry_count"] == 0
        assert dun["next_retry_at"] is not None
        assert dun["grace_until"] is not None
        assert dun["last_error_sanitized"]

        inv_pd = client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=org_h)
        assert inv_pd.json()["status"] == "past_due"

        sub_pd = client.get(f"/api/v1/subscriptions/{subscription_id}", headers=org_h)
        assert sub_pd.status_code == 200, sub_pd.text
        assert sub_pd.json()["status"] == "past_due"
        assert sub_pd.json()["access_state"] == "limited"

        # Concurrent double retry: lock then second retry fails
        r1 = client.post(
            f"/api/v1/billing/payment-attempts/{attempt_id}/retry",
            headers=org_h,
            json={"idempotency_key": f"gp-retry-a-{suffix}"},
        )
        assert r1.status_code == 201, r1.text
        retry_id = r1.json()["id"]

        # Force lock and assert concurrent prevention via begin_retry use case
        with using_write_conn() as conn:
            from app.packages.billing.application.dunning import DunningUseCases
            from app.packages.billing.domain.errors import InvalidTransitionError

            duc = DunningUseCases(conn)
            d = duc.get_by_invoice(org_id, invoice_id)
            assert d is not None
            duc.begin_retry(
                d.id,
                organization_id=org_id,
                actor_user_id=user_id,
            )
            with pytest.raises(InvalidTransitionError):
                duc.begin_retry(
                    d.id,
                    organization_id=org_id,
                    actor_user_id=user_id,
                )
            # release lock for recovery path
            duc.complete_retry_started(d.id, organization_id=org_id, attempt_id=retry_id)

        # Confirm mock payment → settle → allocate → reconcile → full access
        confirmed = client.post(
            f"/api/v1/billing/payment-attempts/{retry_id}/confirm",
            headers=org_h,
        )
        assert confirmed.status_code == 200, confirmed.text

        pays = client.get("/api/v1/billing/payments", headers=org_h)
        assert pays.status_code == 200, pays.text
        payment_items = pays.json().get("items") or []
        payment = next(
            (p for p in payment_items if p.get("payment_attempt_id") == retry_id),
            payment_items[0] if payment_items else None,
        )
        assert payment is not None, pays.text
        payment_id = payment["id"]

        settled = client.post(f"/api/v1/billing/payments/{payment_id}/settle", headers=org_h)
        assert settled.status_code == 200, settled.text

        allocated = client.post(
            f"/api/v1/billing/payments/{payment_id}/allocate",
            headers=org_h,
            json={"invoice_id": invoice_id, "amount": "99.00"},
        )
        assert allocated.status_code in (200, 201), allocated.text

        reconciled = client.post(
            f"/api/v1/billing/payments/{payment_id}/reconcile",
            headers=org_h,
        )
        assert reconciled.status_code == 200, reconciled.text

        dun_rec = client.get(
            f"/api/v1/billing/dunning/by-invoice/{invoice_id}",
            headers=org_h,
        )
        assert dun_rec.json()["status"] == "recovered"

        sub_ok = client.get(f"/api/v1/subscriptions/{subscription_id}", headers=org_h)
        assert sub_ok.json()["status"] == "active"
        assert sub_ok.json()["access_state"] == "full"

        # ── Strategic MRR/ARR ──
        dash = client.get("/api/v1/business-analytics/dashboard", headers=org_h)
        assert dash.status_code == 200, dash.text
        body = dash.json()
        recurring = body.get("recurring_revenue") or {}
        assert recurring.get("active_mrr") == 99.0 or (
            body.get("kpis", {}).get("active_mrr", {}).get("value") == 99.0
        )
        assert recurring.get("active_arr") == 1188.0 or (
            body.get("kpis", {}).get("active_arr", {}).get("value") == 1188.0
        )

        # ── Report → decision → CS → support ──
        d = client.post(
            "/api/v1/reports/definitions",
            headers=org_h,
            json={"code": f"gp-c-{suffix}", "title": "GP Commercial Report"},
        )
        assert d.status_code == 201, d.text
        g = client.post(
            "/api/v1/reports/generations",
            headers=org_h,
            json={"definition_id": d.json()["id"]},
        )
        assert g.status_code == 201, g.text
        gen = client.post(
            f"/api/v1/reports/generations/{g.json()['id']}/generate",
            headers=org_h,
        )
        assert gen.status_code == 200, gen.text
        report_id = gen.json()["executive_report"]["id"]
        assert client.post(
            f"/api/v1/reports/executive/{report_id}/approve", headers=org_h, json={}
        ).status_code == 200
        assert client.post(
            f"/api/v1/reports/executive/{report_id}/publish", headers=org_h
        ).status_code == 200
        dec = client.post(
            "/api/v1/business-decisions",
            headers=org_h,
            json={
                "title": "GP Commercial Decision",
                "proposal": "Retain customer after recovery",
                "executive_report_id": report_id,
            },
        )
        assert dec.status_code == 201, dec.text

        assert client.post(
            "/api/v1/customer-success/health/calculate", headers=org_h
        ).status_code == 200
        case = client.post(
            "/api/v1/support/cases",
            headers=org_h,
            json={"subject": "GP post-recovery support", "priority": "normal"},
        )
        assert case.status_code == 201, case.text
        assert client.post(
            f"/api/v1/support/cases/{case.json()['id']}/resolve", headers=org_h
        ).status_code == 200

    def test_logout_clears_me(self, client: TestClient, golden_path_ctx: dict) -> None:
        login = client.post(
            "/api/v1/users/login",
            json={"login": "admin", "password": "admin123", "remember": True},
        )
        assert login.status_code == 200
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/users/me", headers=headers).status_code == 200
        logout = client.post("/api/v1/users/logout", headers=headers)
        assert logout.status_code in (200, 204)
        me = client.get("/api/v1/users/me", headers=headers)
        assert me.status_code == 401
