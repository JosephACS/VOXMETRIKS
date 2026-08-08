# -*- coding: utf-8 -*-
"""Validate all 33 simple reports respond without 500."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.simple_reports.registry import all_reports

_STAFF_USER_ID = 1


def _ensure_active_org_for_user(user_id: int = _STAFF_USER_ID) -> int:
    now = utc_now()
    slug = f"simple-reports-all-org-u{user_id}"
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
            VALUES (?, 'All Reports Org', 'All Reports Org LLC', ?, 'label', 'US',
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


def test_all_simple_reports_data_endpoint(client: TestClient):
    from app.main import app
    from app.packages.identity.services.auth_deps import (
        require_staff_identity,
        require_user_id,
    )
    from app.packages.simple_reports.presentation.dependencies import get_current_role

    org_id = _ensure_active_org_for_user()
    app.dependency_overrides[require_user_id] = lambda: _STAFF_USER_ID
    app.dependency_overrides[require_staff_identity] = lambda: _STAFF_USER_ID
    app.dependency_overrides[get_current_role] = lambda: "admin"
    try:
        reports = all_reports()
        assert len(reports) == 33
        failures = []
        for r in reports:
            headers = {"X-Organization-Id": str(org_id)} if r.org_scoped else {}
            resp = client.get(
                f"/api/v1/reports/simple/{r.id}/data",
                params={"page": 1, "page_size": 5},
                headers=headers,
            )
            if resp.status_code != 200:
                failures.append((r.id, resp.status_code, resp.text[:200]))
                continue
            body = resp.json()
            if body.get("report_id") != r.id:
                failures.append((r.id, "bad_id", body.get("report_id")))
            if "columns" not in body or "items" not in body:
                failures.append((r.id, "shape", list(body.keys())))
        assert not failures, failures
    finally:
        app.dependency_overrides.clear()
