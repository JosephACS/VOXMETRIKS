"""Test M5: Artists security — Spec 020.

Covers:
- Cross-tenant isolation (org A cannot read/mutate org B artists) at use-case layer
- Missing artist.* permission -> 403 at API layer
- Permission-denied for viewer role trying to create/assign/archive
- Audit entries written for create/transition/transfer
- Optional warehouse link never mutates dim_artista
"""

from __future__ import annotations

import uuid

import duckdb
import pytest
from fastapi.testclient import TestClient


# ── Fixture: isolated DB for use-case level security tests ────────────────────

@pytest.fixture(scope="module")
def sec_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("artists_sec") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)

    conn.execute("""
        CREATE TABLE dim_artista (
            id_artista     INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
    """)
    conn.execute("INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (1, 'Warehouse Artist')")

    ensure_artist_tables(conn)

    # Restore the global schema-ready flag immediately (rather than at
    # teardown): it must only be False for the duration of this fixture's
    # own ensure_* calls against its private tmp-path connection. This file
    # also has client-based tests (viewer_context) that share the process
    # and would otherwise see schema_ready()==False for the whole module,
    # causing them to (incorrectly) re-run CREATE TABLE against the shared
    # read-only test-session connection.
    schema_bootstrap._schema_ready = previous

    now = utc_now()
    for oid, slug in [(400, "sec-org-a-art"), (401, "sec-org-b-art")]:
        conn.execute("""
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, NULL, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
        """, [oid, f"Sec Org {slug}", slug, now, now])

    yield conn
    conn.close()


# ── Cross-tenant isolation ─────────────────────────────────────────────────────

def test_cross_tenant_get_blocked(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import NotFoundError

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Sec Artist {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(NotFoundError):
        ArtistProfileUseCases(sec_conn).get(artist.id, organization_id=401)


def test_cross_tenant_activate_blocked(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import NotFoundError

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Sec Artist 2 {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(NotFoundError):
        ArtistProfileUseCases(sec_conn).activate(artist.id, actor_user_id=1, organization_id=401)


def test_cross_tenant_assignment_blocked(sec_conn):
    from app.packages.artists.application.use_cases import ArtistAssignmentUseCases
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import NotFoundError

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Sec Artist 3 {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(NotFoundError):
        ArtistAssignmentUseCases(sec_conn).assign_manager(
            artist.id, actor_user_id=1, organization_id=401, user_id=99,
        )


def test_duplicate_scoped_per_org_not_cross_org(sec_conn):
    """Same normalized name in two different orgs is allowed (no cross-org leakage)."""
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    name = f"Cross Org Name {uuid.uuid4().hex[:8]}"
    a1 = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=name,
    )
    a2 = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=401, display_name=name,
    )
    assert a1.id != a2.id
    assert a1.organization_id != a2.organization_id


# ── Warehouse isolation ────────────────────────────────────────────────────────

def test_link_warehouse_artist_does_not_mutate_dim_artista(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    before = sec_conn.execute("SELECT nombre_artista FROM dim_artista WHERE id_artista = 1").fetchone()[0]
    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Warehouse Link {uuid.uuid4().hex[:8]}",
    )
    ArtistProfileUseCases(sec_conn).link_warehouse_artist(
        artist.id, actor_user_id=1, organization_id=400, warehouse_artist_id=1,
    )
    after = sec_conn.execute("SELECT nombre_artista FROM dim_artista WHERE id_artista = 1").fetchone()[0]
    assert before == after
    count = sec_conn.execute("SELECT COUNT(*) FROM dim_artista").fetchone()[0]
    assert int(count) == 1


# ── Audit entries ───────────────────────────────────────────────────────────────

def test_audit_entry_on_create(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Audited Create {uuid.uuid4().hex[:8]}",
    )
    row = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'artist_profile' "
        "AND target_id = ? AND action = 'artist_profile.created'",
        [str(artist.id)],
    ).fetchone()
    assert row is not None


def test_audit_entry_on_status_transition(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Audited Transition {uuid.uuid4().hex[:8]}",
    )
    ArtistProfileUseCases(sec_conn).activate(artist.id, actor_user_id=1, organization_id=400)
    row = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'artist_profile' "
        "AND target_id = ? AND action = 'artist_profile.active'",
        [str(artist.id)],
    ).fetchone()
    assert row is not None


def test_audit_entry_on_transfer(sec_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    artist = ArtistProfileUseCases(sec_conn).create(
        actor_user_id=1, organization_id=400, display_name=f"Audited Transfer {uuid.uuid4().hex[:8]}",
    )
    ArtistProfileUseCases(sec_conn).transfer_organization(
        artist.id, actor_user_id=1, organization_id=400, target_organization_id=401,
        reason="security test transfer",
    )
    row = sec_conn.execute(
        "SELECT reason FROM app_audit_log WHERE target_type = 'artist_profile' "
        "AND target_id = ? AND action = 'artist_profile.transferred'",
        [str(artist.id)],
    ).fetchone()
    assert row is not None
    assert row[0] == "security test transfer"


# ── API-level permission denial ────────────────────────────────────────────────

@pytest.fixture(scope="module")
def viewer_context(client: TestClient) -> dict:
    """Login as demo user, add as 'viewer' member of a fresh org."""
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    body = resp.json()
    token = body["token"]
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None

    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = 'artists-sec-viewer-org-m5'"
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (220, 'Artists Sec Viewer Org M5', NULL, 'artists-sec-viewer-org-m5', 'label', 'US',
                        'UTC', 'USD', 'active', ?, ?, ?)
            """, [int(user_id), now, now])
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 220 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute("""
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 220, ?, 'active', ?, ?, ?)
            """, [next_mid, int(user_id), int(user_id), now, now])

            viewer_role_id = conn.execute(
                "SELECT id FROM app_business_role WHERE code = 'viewer'"
            ).fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute("""
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, [next_mrid, next_mid, int(viewer_role_id), int(user_id), now])

    return {"headers": headers, "user_id": user_id, "org_id": 220,
            "org_headers": {**headers, "X-Organization-Id": "220"}}


def test_viewer_can_view_but_not_create(client: TestClient, viewer_context):
    r_list = client.get("/api/v1/artists", headers=viewer_context["org_headers"])
    assert r_list.status_code == 200, r_list.text

    r_create = client.post(
        "/api/v1/artists",
        json={"display_name": "Should Be Denied"},
        headers=viewer_context["org_headers"],
    )
    assert r_create.status_code == 403, r_create.text


def test_viewer_cannot_assign_or_archive(client: TestClient, viewer_context):
    r_assign = client.post(
        "/api/v1/artists/1/assignments",
        json={"user_id": 1, "role": "manager"},
        headers=viewer_context["org_headers"],
    )
    assert r_assign.status_code == 403, r_assign.text

    r_archive = client.post(
        "/api/v1/artists/1/archive", json={},
        headers=viewer_context["org_headers"],
    )
    assert r_archive.status_code == 403, r_archive.text
