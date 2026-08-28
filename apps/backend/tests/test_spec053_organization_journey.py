"""Spec 053 — Organization Journey directed tests (session temp DuckDB)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def test_catalogs_endpoint(client: TestClient):
    cats = client.get("/api/v1/organizations/catalogs")
    assert cats.status_code == 200
    body = cats.json()
    assert any(t["code"] == "label" for t in body["organization_types"])
    assert any(c["code"] == "EC" for c in body["countries"])
    assert len(body["countries"]) >= 30
    assert {"BR", "CA", "GB", "JP", "IN"} <= {
        country["code"] for country in body["countries"]
    }
    assert {"BRL", "CAD", "GBP", "JPY", "INR"} <= {
        currency["code"] for currency in body["currencies"]
    }


def test_create_defaults_intent_and_journey(
    client: TestClient, auth_headers: dict[str, str]
):
    intent = f"intent-{uuid.uuid4()}"
    r1 = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Acme Music 053",
            "organization_type": "label",
            "country_code": "EC",
            "client_intent_id": intent,
        },
    )
    assert r1.status_code == 201, r1.text
    data = r1.json()
    org_id = data["organization"]["id"]
    assert data["next_action"]
    assert data["journey_url"]
    assert data["organization"]["timezone"] == "America/Guayaquil"
    assert data["organization"]["default_currency"] == "USD"
    assert data["journey"]["next_action"] == data["next_action"]

    r2 = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Acme Music 053",
            "organization_type": "label",
            "country_code": "EC",
            "client_intent_id": intent,
        },
    )
    assert r2.status_code == 201
    assert r2.json()["reused_existing"] is True
    assert r2.json()["organization"]["id"] == org_id

    bad = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Bad",
            "organization_type": "not-a-type",
            "client_intent_id": f"bad-{uuid.uuid4()}",
        },
    )
    assert bad.status_code == 400
    body = bad.json()
    code = (body.get("details") or {}).get("code") or (body.get("detail") or {}).get("code")
    assert code == "invalid_catalog_value"


def test_journey_complete_requires_plan(
    client: TestClient, auth_headers: dict[str, str]
):
    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Journey Org 053",
            "organization_type": "label",
            "country_code": "MX",
            "client_intent_id": f"j-{uuid.uuid4()}",
        },
    )
    assert created.status_code == 201, created.text
    org_id = created.json()["organization"]["id"]

    j = client.get(f"/api/v1/organizations/{org_id}/journey", headers=auth_headers)
    assert j.status_code == 200
    payload = j.json()
    assert payload["next_action"] in {
        "review_profile",
        "choose_plan",
        "invite_team",
        "complete",
        "enter_workspace",
    }

    miss = client.post(
        f"/api/v1/organizations/{org_id}/journey/complete",
        headers=auth_headers,
        json={"idempotency_key": "k1", "team_step_skipped": True},
    )
    assert miss.status_code == 409
    body = miss.json()
    code = (body.get("details") or {}).get("code") or (body.get("detail") or {}).get("code")
    assert code == "journey_prerequisite_missing"

    roles = client.get(
        f"/api/v1/organizations/{org_id}/invitation-roles", headers=auth_headers
    )
    assert roles.status_code == 200
    codes = {i["code"] for i in roles.json()["items"]}
    assert "viewer" in codes
    assert "owner" not in codes


def test_invitation_token_delivery_mode_fail_closed(monkeypatch: pytest.MonkeyPatch):
    from app.packages.organizations.presentation.router import (
        _invite_token_for_response,
    )

    class _EmailOnly:
        e2e_mode = False
        organization_invitation_delivery_mode = "email_only"
        is_production = False

    class _LocalOnce:
        e2e_mode = False
        organization_invitation_delivery_mode = "local_once"
        is_production = True

    class _E2E:
        e2e_mode = True
        organization_invitation_delivery_mode = "email_only"
        is_production = True

    monkeypatch.setattr(
        "app.packages.organizations.presentation.router.get_settings",
        lambda: _EmailOnly(),
    )
    assert _invite_token_for_response("secret-token") is None

    monkeypatch.setattr(
        "app.packages.organizations.presentation.router.get_settings",
        lambda: _LocalOnce(),
    )
    assert _invite_token_for_response("secret-token") == "secret-token"

    monkeypatch.setattr(
        "app.packages.organizations.presentation.router.get_settings",
        lambda: _E2E(),
    )
    assert _invite_token_for_response("secret-token") == "secret-token"


def test_member_presentation(client: TestClient, auth_headers: dict[str, str]):
    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Members Org 053",
            "organization_type": "distributor",
            "client_intent_id": f"m-{uuid.uuid4()}",
        },
    )
    org_id = created.json()["organization"]["id"]
    members = client.get(
        f"/api/v1/organizations/{org_id}/members", headers=auth_headers
    )
    assert members.status_code == 200
    item = members.json()["items"][0]
    assert item["user"]["display_name"]
    assert "roles" in item
    assert item.get("status_label")


def test_foreign_org_journey_isolation(
    client: TestClient, auth_headers: dict[str, str], admin_auth_headers: dict[str, str]
):
    a = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "A Org 053",
            "organization_type": "label",
            "client_intent_id": f"a-{uuid.uuid4()}",
        },
    )
    assert a.status_code == 201
    a_id = a.json()["organization"]["id"]
    denied = client.get(
        f"/api/v1/organizations/{a_id}/journey", headers=admin_auth_headers
    )
    assert denied.status_code in {403, 404}


def test_enter_workspace_requires_operational_tier_not_completed_flag(
    client: TestClient, auth_headers: dict[str, str]
):
    from app.core.config import get_settings
    import duckdb

    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Completed NonOps 053",
            "organization_type": "label",
            "client_intent_id": f"cno-{uuid.uuid4()}",
        },
    )
    assert created.status_code == 201
    org_id = created.json()["organization"]["id"]
    conn = duckdb.connect(str(get_settings().db_path_resolved))
    try:
        conn.execute(
            """
            UPDATE app_organization_onboarding
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE organization_id = ?
            """,
            [org_id],
        )
    finally:
        conn.close()

    j = client.get(f"/api/v1/organizations/{org_id}/journey", headers=auth_headers)
    assert j.status_code == 200
    body = j.json()
    assert body["onboarding_status"] == "completed"
    assert body["capabilities"]["enter_workspace"] is False
    assert body["next_action"] != "enter_workspace"


def test_journey_get_does_not_run_ddl_or_ensure(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
):
    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "ReadOnly Journey 053",
            "organization_type": "label",
            "client_intent_id": f"ro-{uuid.uuid4()}",
        },
    )
    org_id = created.json()["organization"]["id"]

    def boom(*_a, **_k):
        raise AssertionError("ensure_organization_tables must not run on GET journey")

    monkeypatch.setattr(
        "app.packages.organizations.infrastructure.schema.ensure_organization_tables",
        boom,
    )
    j = client.get(f"/api/v1/organizations/{org_id}/journey", headers=auth_headers)
    assert j.status_code == 200
    roles = client.get(
        f"/api/v1/organizations/{org_id}/invitation-roles", headers=auth_headers
    )
    assert roles.status_code == 200


def test_skip_team_rollback_when_audit_fails(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
):
    from app.core.config import get_settings
    import duckdb
    from app.packages.organizations.infrastructure.repositories.audit_repository import (
        AuditRepository,
    )

    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Audit Rollback 053",
            "organization_type": "label",
            "client_intent_id": f"ar-{uuid.uuid4()}",
        },
    )
    org_id = created.json()["organization"]["id"]

    original_append = AuditRepository.append

    def fail_append(self, *args, **kwargs):
        action = kwargs.get("action")
        if action is None and args:
            action = args[0] if not isinstance(args[0], AuditRepository) else (
                args[1] if len(args) > 1 else ""
            )
        if action == "organization.journey_team_skipped":
            raise RuntimeError("injected audit failure")
        return original_append(self, *args, **kwargs)

    monkeypatch.setattr(AuditRepository, "append", fail_append)

    skip = client.post(
        f"/api/v1/organizations/{org_id}/journey/skip-team", headers=auth_headers
    )
    assert skip.status_code >= 400

    conn = duckdb.connect(str(get_settings().db_path_resolved))
    try:
        row = conn.execute(
            "SELECT team_step_skipped_at, status FROM app_organization_onboarding WHERE organization_id = ?",
            [org_id],
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] is None
    assert row[1] != "completed"


def test_complete_rollback_when_audit_fails(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
):
    """Injected audit failure must roll back onboarding completion."""
    from app.core.config import get_settings
    import duckdb
    from app.packages.organizations.application import journey as journey_mod
    from app.packages.organizations.infrastructure.repositories.audit_repository import (
        AuditRepository,
    )

    created = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Complete Audit Rollback 053",
            "organization_type": "label",
            "client_intent_id": f"car-{uuid.uuid4()}",
        },
    )
    org_id = created.json()["organization"]["id"]

    real_get_journey = journey_mod.get_journey

    def fake_get_journey(conn, *, actor_user_id, organization_id, permissions):
        payload = real_get_journey(
            conn,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            permissions=permissions,
        )
        payload = dict(payload)
        payload["onboarding_status"] = "in_progress"
        payload["access_tier"] = "operational"
        caps = dict(payload["capabilities"])
        caps["complete_journey"] = True
        caps["enter_workspace"] = True
        payload["capabilities"] = caps
        return payload

    monkeypatch.setattr(journey_mod, "get_journey", fake_get_journey)
    monkeypatch.setattr(
        "app.packages.organizations.application.journey.get_org_subscription_snapshot",
        lambda *_a, **_k: {"status": "active", "tier": "operational", "subscription_id": 1},
    )

    original_append = AuditRepository.append

    def fail_append(self, *args, **kwargs):
        action = kwargs.get("action")
        if action == "organization.journey_completed":
            raise RuntimeError("injected audit failure")
        return original_append(self, *args, **kwargs)

    monkeypatch.setattr(AuditRepository, "append", fail_append)

    complete = client.post(
        f"/api/v1/organizations/{org_id}/journey/complete",
        headers=auth_headers,
        json={"idempotency_key": f"k-{uuid.uuid4()}", "team_step_skipped": True},
    )
    assert complete.status_code >= 400

    conn = duckdb.connect(str(get_settings().db_path_resolved))
    try:
        row = conn.execute(
            "SELECT status, team_step_skipped_at FROM app_organization_onboarding WHERE organization_id = ?",
            [org_id],
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == "in_progress"
    assert row[1] is None


def test_create_intent_idempotency_and_slug_rules(
    client: TestClient, auth_headers: dict[str, str]
):
    intent = f"idem-{uuid.uuid4()}"
    payload = {
        "display_name": "Same Intent Org",
        "organization_type": "label",
        "country_code": "EC",
        "client_intent_id": intent,
    }
    r1 = client.post("/api/v1/organizations", headers=auth_headers, json=payload)
    assert r1.status_code == 201
    org_id = r1.json()["organization"]["id"]
    r2 = client.post("/api/v1/organizations", headers=auth_headers, json=payload)
    assert r2.status_code == 201
    assert r2.json()["organization"]["id"] == org_id
    assert r2.json()["reused_existing"] is True

    mismatch = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            **payload,
            "display_name": "Different Payload Same Intent",
        },
    )
    assert mismatch.status_code == 409
    code = (mismatch.json().get("detail") or {}).get("code") or (
        mismatch.json().get("details") or {}
    ).get("code")
    assert code == "intent_payload_mismatch"

    first = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Explicit Slug A",
            "slug": f"explicit-slug-{uuid.uuid4().hex[:8]}",
            "organization_type": "label",
            "client_intent_id": f"ex1-{uuid.uuid4()}",
        },
    )
    assert first.status_code == 201
    slug = first.json()["organization"]["slug"]
    conflict = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": "Explicit Slug B",
            "slug": slug,
            "organization_type": "label",
            "client_intent_id": f"ex2-{uuid.uuid4()}",
        },
    )
    assert conflict.status_code == 409

    name = f"Auto Suffix {uuid.uuid4().hex[:6]}"
    a = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": name,
            "organization_type": "label",
            "client_intent_id": f"auto1-{uuid.uuid4()}",
        },
    )
    b = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "display_name": name,
            "organization_type": "label",
            "client_intent_id": f"auto2-{uuid.uuid4()}",
        },
    )
    assert a.status_code == 201 and b.status_code == 201
    assert a.json()["organization"]["id"] != b.json()["organization"]["id"]
    assert a.json()["organization"]["slug"] != b.json()["organization"]["slug"]


def test_capability_matrix_subscription_create_only():
    from app.packages.organizations.application.journey import _capabilities

    base = dict(
        access_tier="onboarding",
        operational_plan=False,
        checkout=None,
        onboarding_status="in_progress",
        can_setup=True,
    )
    owner = _capabilities(permissions={"subscription.create", "organization.update"}, **base)
    assert owner["choose_plan"] is True
    assert owner["resume_checkout"] is False

    billing_only = _capabilities(
        permissions={"billing.manage", "billing.view", "subscription.create"}, **base
    )
    assert billing_only["choose_plan"] is True

    administrator = _capabilities(
        permissions={"organization.update", "billing.view", "member.invite"}, **base
    )
    assert administrator["choose_plan"] is False
    assert administrator["resume_checkout"] is False

    viewer = _capabilities(permissions={"organization.view", "member.view"}, **base)
    assert viewer["choose_plan"] is False
    assert viewer["enter_workspace"] is False

    resume = _capabilities(
        permissions={"subscription.create"},
        access_tier="onboarding",
        operational_plan=False,
        checkout={"status": "failed", "id": 1},
        onboarding_status="in_progress",
        can_setup=True,
    )
    assert resume["resume_checkout"] is True
    assert resume["choose_plan"] is False

    completed_non_ops = _capabilities(
        permissions={"subscription.create", "organization.update"},
        access_tier="onboarding",
        operational_plan=False,
        checkout=None,
        onboarding_status="completed",
        can_setup=True,
    )
    assert completed_non_ops["enter_workspace"] is False

    operational = _capabilities(
        permissions={"member.view"},
        access_tier="operational",
        operational_plan=True,
        checkout=None,
        onboarding_status="completed",
        can_setup=False,
    )
    assert operational["enter_workspace"] is True
    assert operational["choose_plan"] is False
