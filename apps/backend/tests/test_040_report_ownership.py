# -*- coding: utf-8 -*-
"""Spec 040 — report ownership coverage and catalog metadata."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.packages.complex_reports.ownership import validate_complex_coverage
from app.packages.complex_reports.registry import all_reports as all_complex
from app.packages.simple_reports.ownership import (
    MODULE_LABELS,
    VALID_MODULES,
    get_simple_ownership,
    validate_simple_coverage,
)
from app.packages.simple_reports.registry import all_reports as all_simple


def test_all_simple_reports_have_unique_ownership():
    ids = [r.id for r in all_simple()]
    assert len(ids) == 33
    assert len(set(ids)) == 33
    errors = validate_simple_coverage(ids)
    assert not errors, errors


def test_all_complex_reports_have_ownership():
    ids = [r.id for r in all_complex()]
    errors = validate_complex_coverage(ids)
    assert not errors, errors


def test_simple_ownership_fields_valid():
    for r in all_simple():
        own = get_simple_ownership(r.id)
        assert own is not None, r.id
        assert own.business_module in VALID_MODULES
        assert own.category
        assert own.business_process
        assert own.decision
        assert own.route
        assert own.data_classification


def test_catalog_exposes_ownership_and_filters(client: TestClient):
    from app.main import app
    from app.packages.identity.services.auth_deps import require_staff_identity, require_user_id
    from app.packages.simple_reports.presentation.dependencies import get_current_role

    app.dependency_overrides[require_user_id] = lambda: 1
    app.dependency_overrides[require_staff_identity] = lambda: 1
    app.dependency_overrides[get_current_role] = lambda: "admin"
    try:
        resp = client.get("/api/v1/reports/simple/catalog")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert body["modules"]
        item = body["items"][0]
        assert item["business_module"] in VALID_MODULES
        assert item["business_module_label"] in MODULE_LABELS.values()
        assert item["category"]
        assert item["route"]

        mod = item["business_module"]
        filtered = client.get(f"/api/v1/reports/simple/catalog?module={mod}")
        assert filtered.status_code == 200
        assert all(i["business_module"] == mod for i in filtered.json()["items"])
        assert filtered.json()["total"] >= 1
    finally:
        app.dependency_overrides.clear()


def test_listener_cannot_list_enterprise_catalog(client: TestClient):
    from app.main import app
    from app.packages.identity.services.auth_deps import require_staff_identity

    def _deny():
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="staff required")

    app.dependency_overrides[require_staff_identity] = _deny
    try:
        resp = client.get("/api/v1/reports/simple/catalog")
        # Authentication is evaluated before the staff-role dependency.
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()
