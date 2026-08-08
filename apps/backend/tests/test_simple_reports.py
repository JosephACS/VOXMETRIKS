# -*- coding: utf-8 -*-
"""Tests for simple reports catalog and data endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.simple_reports.registry import REPORTS, all_reports, get_report

_STAFF_USER_ID = 1


def _ensure_active_org_for_user(user_id: int = _STAFF_USER_ID) -> int:
    """Create (or reuse) an active org membership for report org-scoped tests."""
    now = utc_now()
    slug = f"simple-reports-org-u{user_id}"
    with using_write_conn() as conn:
        row = conn.execute(
            """
            SELECT o.id
            FROM app_organization o
            JOIN app_organization_member m ON m.organization_id = o.id
            WHERE m.user_id = ? AND m.status = 'active' AND o.status = 'active'
            LIMIT 1
            """,
            [user_id],
        ).fetchone()
        if row:
            return int(row[0])

        org_id = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, 'Simple Reports Org', 'Simple Reports Org LLC', ?, 'label', 'US',
                    'UTC', 'USD', 'active', ?, ?, ?)
            """,
            [org_id, slug, user_id, now, now],
        )
        mid = int(
            conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0]
        )
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, joined_at, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [mid, org_id, user_id, now, user_id, now, now],
        )
        return org_id


def _ensure_foreign_org(actor_user_id: int = _STAFF_USER_ID) -> int:
    """Org that exists but where actor is not an active member."""
    now = utc_now()
    with using_write_conn() as conn:
        org_id = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, 'Foreign Org', 'Foreign Org LLC', ?, 'label', 'US',
                    'UTC', 'USD', 'active', ?, ?, ?)
            """,
            [org_id, f"foreign-org-{org_id}", actor_user_id, now, now],
        )
        return org_id


def _staff_overrides(app):
    from app.packages.identity.services.auth_deps import (
        require_staff_identity,
        require_user_id,
    )
    from app.packages.simple_reports.presentation.dependencies import get_current_role

    app.dependency_overrides[require_user_id] = lambda: _STAFF_USER_ID
    app.dependency_overrides[require_staff_identity] = lambda: _STAFF_USER_ID
    app.dependency_overrides[get_current_role] = lambda: "admin"
    return require_user_id, require_staff_identity, get_current_role


def _clear_overrides(app, *deps):
    for d in deps:
        app.dependency_overrides.pop(d, None)


def _headers_for(report_id: str, org_id: int | None) -> dict[str, str]:
    report = get_report(report_id)
    if report and report.org_scoped:
        assert org_id is not None
        return {"X-Organization-Id": str(org_id)}
    return {}


def test_registry_has_33_reports():
    assert len(REPORTS) == 33
    assert len(all_reports()) == 33
    ids = [r.id for r in all_reports()]
    assert len(ids) == len(set(ids))


def test_catalog_requires_auth(client: TestClient):
    r = client.get("/api/v1/reports/simple/catalog")
    assert r.status_code in (401, 403)


def test_catalog_and_unknown_report(client: TestClient):
    from app.main import app
    from fastapi import HTTPException
    from app.packages.identity.services.auth_deps import require_staff_identity

    org_id = _ensure_active_org_for_user()
    deps = _staff_overrides(app)
    try:
        r = client.get("/api/v1/reports/simple/catalog")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 33
        assert len(body["items"]) == 33

        bad = client.get("/api/v1/reports/simple/does-not-exist/data")
        assert bad.status_code == 404

        # Prefer a global report for catalog smoke when available.
        sample = next((i for i in body["items"] if not i.get("org_scoped")), body["items"][0])
        headers = _headers_for(sample["id"], org_id)
        data = client.get(
            f"/api/v1/reports/simple/{sample['id']}/data",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )
        assert data.status_code == 200
        payload = data.json()
        assert payload["report_id"] == sample["id"]
        assert "items" in payload
        assert payload["page"] == 1
        assert "columns" in payload
        assert "data_classification" in payload

        def _deny():
            raise HTTPException(status_code=403, detail="Staff role required")

        app.dependency_overrides[require_staff_identity] = _deny
        limited = client.get("/api/v1/reports/simple/catalog")
        assert limited.status_code == 403
    finally:
        _clear_overrides(app, *deps)


def test_invalid_page_size(client: TestClient):
    from app.main import app

    # Global report so FastAPI reaches Query(le=100) validation (422), not org 400.
    rid = "sessions-active"
    assert get_report(rid) is not None
    assert get_report(rid).org_scoped is False

    deps = _staff_overrides(app)
    try:
        r = client.get(f"/api/v1/reports/simple/{rid}/data", params={"page_size": 9999})
        assert r.status_code == 422
    finally:
        _clear_overrides(app, *deps)


def test_org_scoped_requires_header(client: TestClient):
    from app.main import app

    rid = "business-alerts-open"
    assert get_report(rid).org_scoped is True
    deps = _staff_overrides(app)
    try:
        r = client.get(f"/api/v1/reports/simple/{rid}/data", params={"page": 1, "page_size": 5})
        assert r.status_code == 400
        body = r.json()
        detail = body.get("detail") or body.get("message") or str(body)
        assert "organización" in str(detail).lower() or "X-Organization-Id" in str(detail)
    finally:
        _clear_overrides(app, *deps)


def test_org_scoped_foreign_org_forbidden(client: TestClient):
    from app.main import app

    rid = "business-alerts-open"
    foreign = _ensure_foreign_org()
    deps = _staff_overrides(app)
    try:
        r = client.get(
            f"/api/v1/reports/simple/{rid}/data",
            params={"page": 1, "page_size": 5},
            headers={"X-Organization-Id": str(foreign)},
        )
        assert r.status_code == 403
    finally:
        _clear_overrides(app, *deps)


def test_org_scoped_member_ok(client: TestClient):
    from app.main import app

    rid = "business-alerts-open"
    org_id = _ensure_active_org_for_user()
    deps = _staff_overrides(app)
    try:
        r = client.get(
            f"/api/v1/reports/simple/{rid}/data",
            params={"page": 1, "page_size": 5},
            headers={"X-Organization-Id": str(org_id)},
        )
        assert r.status_code == 200, r.text
        assert r.json()["report_id"] == rid
    finally:
        _clear_overrides(app, *deps)


def test_global_report_without_header_ok(client: TestClient):
    from app.main import app

    rid = "sessions-active"
    assert get_report(rid).org_scoped is False
    deps = _staff_overrides(app)
    try:
        r = client.get(f"/api/v1/reports/simple/{rid}/data", params={"page": 1, "page_size": 5})
        assert r.status_code == 200, r.text
        assert r.json()["report_id"] == rid
    finally:
        _clear_overrides(app, *deps)


def test_several_domain_reports_return_shape(client: TestClient):
    from app.main import app

    org_id = _ensure_active_org_for_user()
    samples = [
        "business-alerts-open",
        "invoices-pending-overdue",
        "tracks-without-cover",
        "sessions-active",
        "etl-loads-failed",
    ]
    deps = _staff_overrides(app)
    try:
        for rid in samples:
            headers = _headers_for(rid, org_id)
            r = client.get(
                f"/api/v1/reports/simple/{rid}/data",
                params={"page": 1, "page_size": 5},
                headers=headers,
            )
            assert r.status_code == 200, (rid, r.status_code, r.text[:200])
            body = r.json()
            assert body["report_id"] == rid
            assert isinstance(body["items"], list)
            assert isinstance(body["total"], int)
    finally:
        _clear_overrides(app, *deps)
