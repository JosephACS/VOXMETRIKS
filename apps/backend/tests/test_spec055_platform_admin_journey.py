# -*- coding: utf-8 -*-
"""Spec 055 — Platform Admin overview, RBAC, availability and mutation hardening."""

from __future__ import annotations

from datetime import datetime, timezone

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.artists.identity_access.errors import ValidationError as ArtistValidationError
from app.packages.artists.identity_access.use_cases import PlatformArtistRequestUseCases
from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.domain.errors import ValidationError as CatalogValidationError
from app.packages.platform_ops.application.overview import build_platform_ops_overview
from app.packages.platform_ops.presentation.schemas import PlatformOpsOverviewOut
from app.packages.platform_rbac.infrastructure.repository import assign_role


@pytest.fixture()
def overview_conn(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXMETRIKS_TEST_ISOLATION", "1")
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    db = tmp_path / "spec055_overview.duckdb"
    conn = duckdb.connect(str(db))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_publishing.infrastructure.schema import (
        ensure_catalog_publishing_tables,
    )
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_ops_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_publishing_tables(conn)
    ensure_platform_rbac_tables(conn)

    # Minimal audio source table for unresolved counts (no warehouse DDL).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_track_audio_source (
            track_id INTEGER,
            provider VARCHAR,
            status VARCHAR
        )
        """
    )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_overview_empty_available_queues(overview_conn):
    data = build_platform_ops_overview(overview_conn)
    out = PlatformOpsOverviewOut.model_validate(data)
    assert out.health in ("healthy", "degraded")
    assert out.has_pending_work is False
    assert out.next_queue is None
    codes = [q.code for q in out.queues]
    assert codes == [
        "artist_requests",
        "catalog_reviews",
        "audio_unresolved",
        "incidents",
    ]
    for q in out.queues:
        assert q.availability == "available"
        assert q.count == 0


def test_overview_unavailable_when_source_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXMETRIKS_TEST_ISOLATION", "1")
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "spec055_empty.duckdb"))
    schema_bootstrap._schema_ready = previous
    try:
        data = build_platform_ops_overview(conn)
        out = PlatformOpsOverviewOut.model_validate(data)
        assert out.health == "unavailable"
        for q in out.queues:
            assert q.availability == "unavailable"
            assert q.count is None
        assert out.has_pending_work is False
        assert out.next_queue is None
    finally:
        conn.close()


def test_overview_priority_next_queue(overview_conn):
    now = utc_now()
    overview_conn.execute(
        """
        INSERT INTO app_artist_access_request (
            id, applicant_user_id, request_type, status,
            target_artist_profile_id, warehouse_artist_id, proposed_display_name,
            proposed_role, relationship_type, evidence_url, evidence_note,
            created_at
        ) VALUES (1, 9, 'claim_ownership', 'pending', NULL, 1, 'Band',
                  'owner', NULL, NULL, NULL, ?)
        """,
        [now],
    )
    overview_conn.execute(
        """
        INSERT INTO app_operational_incident (
            id, title, severity, status, description, reported_by,
            reported_at, resolved_at, created_at, updated_at
        ) VALUES (1, 'Incident', 'high', 'open', 'x', 1, ?, NULL, ?, ?)
        """,
        [now, now, now],
    )
    data = build_platform_ops_overview(overview_conn)
    out = PlatformOpsOverviewOut.model_validate(data)
    assert out.next_queue == "artist_requests"
    assert out.has_pending_work is True
    artist_q = next(q for q in out.queues if q.code == "artist_requests")
    assert artist_q.count == 1
    assert artist_q.severity == "attention"


def test_overview_skips_unavailable_when_picking_next(overview_conn):
    # Drop artist table → unavailable; seed incidents → next should be incidents
    overview_conn.execute("DROP TABLE app_artist_access_request")
    now = utc_now()
    overview_conn.execute(
        """
        INSERT INTO app_operational_incident (
            id, title, severity, status, description, reported_by,
            reported_at, resolved_at, created_at, updated_at
        ) VALUES (2, 'Open', 'medium', 'investigating', 'y', 1, ?, NULL, ?, ?)
        """,
        [now, now, now],
    )
    data = build_platform_ops_overview(overview_conn)
    out = PlatformOpsOverviewOut.model_validate(data)
    artist_q = next(q for q in out.queues if q.code == "artist_requests")
    assert artist_q.count is None
    assert artist_q.availability == "unavailable"
    assert out.next_queue == "incidents"


def _admin_headers(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = body["token"]
    user_id = body.get("id") or (body.get("user") or {}).get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json().get("id")
    with using_write_conn() as conn:
        assign_role(conn, user_id=int(user_id), role_code="platform_admin", assigned_by=None)
    return {"Authorization": f"Bearer {token}"}


def test_overview_api_rbac(client: TestClient):
    denied = client.get("/api/v1/platform-ops/overview")
    assert denied.status_code in (401, 403)

    demo = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    if demo.status_code == 200:
        token = demo.json()["token"]
        forbidden = client.get(
            "/api/v1/platform-ops/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert forbidden.status_code == 403

    headers = _admin_headers(client)
    ok = client.get("/api/v1/platform-ops/overview", headers=headers)
    assert ok.status_code == 200, ok.text
    body = ok.json()
    PlatformOpsOverviewOut.model_validate(body)
    assert "queues" in body
    assert set(body.keys()) == {
        "health",
        "generated_at",
        "queues",
        "next_queue",
        "has_pending_work",
    }
    for q in body["queues"]:
        assert set(q.keys()) == {"code", "count", "availability", "severity"}


def test_artist_reject_requires_reason_and_no_partial_write(overview_conn):
    now = utc_now()
    overview_conn.execute(
        """
        INSERT INTO app_artist_access_request (
            id, applicant_user_id, request_type, status,
            target_artist_profile_id, warehouse_artist_id, proposed_display_name,
            proposed_role, relationship_type, evidence_url, evidence_note,
            created_at
        ) VALUES (10, 2, 'create_new', 'pending', NULL, NULL, 'New Act',
                  'owner', NULL, NULL, NULL, ?)
        """,
        [now],
    )
    # Prefer seeded identity admin (id=1) when present; otherwise insert.
    existing = overview_conn.execute(
        "SELECT id, role FROM app_user WHERE id = 1"
    ).fetchone()
    if existing:
        overview_conn.execute("UPDATE app_user SET role = 'admin' WHERE id = 1")
        admin_id = 1
    else:
        overview_conn.execute(
            """
            INSERT INTO app_user (id, username, email, password_hash, role, created_at)
            VALUES (1, 'admin', 'admin@test.local', 'x', 'admin', ?)
            """,
            [now],
        )
        admin_id = 1

    uc = PlatformArtistRequestUseCases(overview_conn)
    with pytest.raises(ArtistValidationError):
        uc.reject(user_id=admin_id, request_id=10, reason="   ")
    row = overview_conn.execute(
        "SELECT status, rejection_reason FROM app_artist_access_request WHERE id = 10"
    ).fetchone()
    assert row[0] == "pending"
    assert row[1] is None

    result = uc.reject(user_id=admin_id, request_id=10, reason="Incomplete evidence")
    assert result["status"] == "rejected"
    row2 = overview_conn.execute(
        "SELECT status, rejection_reason FROM app_artist_access_request WHERE id = 10"
    ).fetchone()
    assert row2[0] == "rejected"
    assert row2[1] == "Incomplete evidence"


def test_catalog_reject_blank_reason_rolls_back_status(overview_conn):
    """Blank reject must raise before state change when already under_review."""
    now = utc_now()
    overview_conn.execute(
        """
        INSERT INTO app_organization (
            id, display_name, legal_name, slug, organization_type, country_code,
            timezone, default_currency, status, created_by, created_at, updated_at
        ) VALUES (77, 'WS', 'WS', 'ws-055', 'artist_workspace', 'US',
                  'UTC', 'USD', 'active', 1, ?, ?)
        """,
        [now, now],
    )
    overview_conn.execute(
        """
        INSERT INTO app_artist_profile (
            id, display_name, normalized_name, status, organization_id,
            created_by, created_at, updated_at
        ) VALUES (5, 'Act', 'act', 'active', 77, 1, ?, ?)
        """,
        [now, now],
    )
    overview_conn.execute(
        """
        INSERT INTO app_release_submission (
            id, organization_id, artist_profile_id, release_type, title, status,
            created_by, is_demo, created_at, updated_at
        ) VALUES (33, 77, 5, 'single', 'Song', 'under_review', 1, FALSE, ?, ?)
        """,
        [now, now],
    )
    uc = CatalogPublishingUseCases(overview_conn)
    with pytest.raises(CatalogValidationError):
        uc.reject(
            submission_id=33,
            organization_id=77,
            actor_user_id=1,
            reason="  ",
        )
    status = overview_conn.execute(
        "SELECT status, reject_reason FROM app_release_submission WHERE id = 33"
    ).fetchone()
    assert status[0] == "under_review"
    assert status[1] is None
