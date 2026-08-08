# -*- coding: utf-8 -*-
"""Spec 044 — multi-org isolation for org-scoped simple reports."""

from __future__ import annotations

import duckdb

from app.packages.simple_reports.queries import (
    _crm_quotations_pending,
    _payment_attempts_failed,
    _release_issues_open,
)
from app.packages.simple_reports.registry import get_report


def test_registry_org_scoped_flags():
    assert get_report("crm-quotations-pending").org_scoped is True
    assert get_report("release-review-issues-open").org_scoped is True
    assert get_report("payment-attempts-failed").org_scoped is True
    assert get_report("data-quality-failed").org_scoped is False


def _mem() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(":memory:")


def test_payment_attempts_isolated_by_org():
    conn = _mem()
    conn.execute(
        """
        CREATE TABLE app_payment_attempt (
            id INTEGER, organization_id INTEGER, invoice_id INTEGER,
            status VARCHAR, failure_reason VARCHAR, created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        "INSERT INTO app_payment_attempt VALUES (1, 10, 100, 'failed', 'x', CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "INSERT INTO app_payment_attempt VALUES (2, 20, 200, 'failed', 'y', CURRENT_TIMESTAMP)"
    )
    assert _payment_attempts_failed(conn, organization_id=None) == []
    a = _payment_attempts_failed(conn, organization_id=10)
    b = _payment_attempts_failed(conn, organization_id=20)
    assert len(a) == 1 and a[0]["invoice_id"] == 100
    assert len(b) == 1 and b[0]["invoice_id"] == 200
    assert _payment_attempts_failed(conn, organization_id=99) == []


def test_release_issues_isolated_by_org():
    conn = _mem()
    conn.execute("CREATE TABLE app_release_submission (id INTEGER, organization_id INTEGER)")
    conn.execute(
        """
        CREATE TABLE app_release_review_issue (
            id INTEGER, submission_id INTEGER, severity VARCHAR,
            message VARCHAR, resolved BOOLEAN
        )
        """
    )
    conn.execute("INSERT INTO app_release_submission VALUES (1, 10), (2, 20)")
    conn.execute(
        "INSERT INTO app_release_review_issue VALUES "
        "(1, 1, 'high', 'a', FALSE), (2, 2, 'low', 'b', FALSE)"
    )
    assert _release_issues_open(conn, organization_id=None) == []
    a = _release_issues_open(conn, organization_id=10)
    b = _release_issues_open(conn, organization_id=20)
    assert len(a) == 1 and a[0]["submission_id"] == 1
    assert len(b) == 1 and b[0]["submission_id"] == 2


def test_crm_quotations_isolated_via_opportunity():
    conn = _mem()
    conn.execute("CREATE TABLE app_crm_opportunity (id INTEGER, organization_id INTEGER)")
    conn.execute("CREATE TABLE app_crm_quotation (id INTEGER, opportunity_id INTEGER)")
    conn.execute(
        """
        CREATE TABLE app_crm_quotation_version (
            id INTEGER, quotation_id INTEGER, status VARCHAR, updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE app_crm_approval_request (
            id INTEGER, object_type VARCHAR, object_id INTEGER,
            status VARCHAR, requested_at TIMESTAMP
        )
        """
    )
    conn.execute("INSERT INTO app_crm_opportunity VALUES (1, 10), (2, 20)")
    conn.execute("INSERT INTO app_crm_quotation VALUES (1, 1), (2, 2)")
    conn.execute(
        "INSERT INTO app_crm_quotation_version VALUES "
        "(11, 1, 'draft', CURRENT_TIMESTAMP), (22, 2, 'draft', CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "INSERT INTO app_crm_approval_request VALUES "
        "(1, 'quotation_version', 11, 'pending', CURRENT_TIMESTAMP), "
        "(2, 'quotation_version', 22, 'pending', CURRENT_TIMESTAMP)"
    )
    assert _crm_quotations_pending(conn, organization_id=None) == []
    a = _crm_quotations_pending(conn, organization_id=10)
    b = _crm_quotations_pending(conn, organization_id=20)
    assert len(a) == 1 and a[0]["object_id"] == 11
    assert len(b) == 1 and b[0]["object_id"] == 22
