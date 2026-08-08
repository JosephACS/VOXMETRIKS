# -*- coding: utf-8 -*-
"""Workpanel and complex reports API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.packages.complex_reports.registry import REPORTS, all_reports


def test_complex_registry_has_essentials():
    ids = {r.id for r in all_reports()}
    assert "income-by-month" in ids
    assert "streams-by-day" in ids
    assert "top-tracks-period" in ids
    assert REPORTS["campaign-roi"].available is False


def test_workpanel_requires_auth(client: TestClient):
    r = client.get("/api/v1/workpanel")
    assert r.status_code in (401, 403)


def test_workpanel_and_complex_catalog(client: TestClient):
    from app.main import app
    from app.packages.complex_reports import router as cr
    from app.packages.identity.services.auth_deps import (
        require_staff_identity,
        require_user_id,
    )
    from app.packages.workpanel import router as wp

    app.dependency_overrides[require_user_id] = lambda: 1
    app.dependency_overrides[require_staff_identity] = lambda: 1
    original_cr = cr._role
    original_wp = wp._role
    cr._role = lambda user_id, conn: "admin"
    wp._role = lambda user_id, conn: "admin"
    try:
        # Default period (no fixed YYYY-MM) — avoid unknown_period on empty warehouse months.
        wp_resp = client.get("/api/v1/workpanel")
        assert wp_resp.status_code == 200, wp_resp.text
        body = wp_resp.json()
        assert body["title"] == "Workpanel"
        assert "metrics" in body
        assert isinstance(body["metrics"], list)
        assert len(body["metrics"]) >= 5
        assert "data_classification" in body
        assert "monetary_classification" in body
        for m in body["metrics"]:
            assert "label" in m
            assert "detail_path" in m
            assert "explanation" in m

        available = body.get("available_periods") or []
        default_period = body.get("default_period")
        if available:
            period = default_period or available[0]
            wp2 = client.get("/api/v1/workpanel", params={"period": period})
            assert wp2.status_code == 200, wp2.text
            assert wp2.json().get("period")

        cat = client.get("/api/v1/reports/complex/catalog")
        assert cat.status_code == 200
        items = cat.json()["items"]
        assert len(items) >= 8

        # Complex date range: use period month when available, else omit fixed far-future month.
        if default_period and len(str(default_period)) == 7:
            y, m = str(default_period).split("-")
            from_date = f"{y}-{m}-01"
            # inclusive end within month is fine for streams-by-day
            to_date = f"{y}-{m}-28"
            streams = client.get(
                "/api/v1/reports/complex/streams-by-day/data",
                params={"from": from_date, "to": to_date},
            )
        else:
            streams = client.get("/api/v1/reports/complex/streams-by-day/data")
        assert streams.status_code == 200, streams.text
        sbody = streams.json()
        assert sbody["report_id"] == "streams-by-day"
        assert "summary" in sbody
        assert "series" in sbody
        assert "data_classification" in sbody

        roi = client.get("/api/v1/reports/complex/campaign-roi/data")
        assert roi.status_code == 200
        assert roi.json()["available"] is False
    finally:
        cr._role = original_cr
        wp._role = original_wp
        app.dependency_overrides.clear()


def test_complex_forbidden_for_user_on_admin_report(client: TestClient):
    from app.main import app
    from app.packages.identity.services.auth_deps import (
        require_staff_identity,
        require_user_id,
    )

    app.dependency_overrides[require_user_id] = lambda: 1

    # Listener must not pass staff gate (403 before role-specific report checks).
    from fastapi import HTTPException

    def _deny_staff():
        raise HTTPException(status_code=403, detail="Staff role required")

    app.dependency_overrides[require_staff_identity] = _deny_staff
    try:
        r = client.get("/api/v1/reports/complex/income-by-month/data")
        assert r.status_code == 403
        assert "metrics" not in (r.json() if r.content else {})
    finally:
        app.dependency_overrides.clear()
