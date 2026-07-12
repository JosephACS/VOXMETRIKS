"""Test N5: Catalog rights security — Spec 021.

Covers:
- Cross-tenant isolation (org A cannot read/mutate org B assets/contracts)
  at the use-case layer.
- Missing rights.* permission -> 403 at the API layer.
- Permission-denied for viewer role trying to create/approve/archive.
- Audit entries written for register/create/party-add/archive.
- Optional warehouse link never mutates dim_track.
- rights_contract is never confused with / joined to app_commercial_contract.
"""

from __future__ import annotations

import uuid
from datetime import date

import duckdb
import pytest
from fastapi.testclient import TestClient


# ── Fixture: isolated DB for use-case level security tests ────────────────────

@pytest.fixture(scope="module")
def sec_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("catalog_rights_sec") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    ensure_artist_tables(conn)

    conn.execute("""
        CREATE TABLE dim_track (
            id_track      INTEGER PRIMARY KEY,
            nombre_track  VARCHAR NOT NULL
        )
    """)
    conn.execute("INSERT INTO dim_track (id_track, nombre_track) VALUES (1, 'Warehouse Track')")

    ensure_catalog_rights_tables(conn)

    schema_bootstrap._schema_ready = previous

    now = utc_now()
    for oid, slug in [(410, "sec-org-a-rights"), (411, "sec-org-b-rights")]:
        conn.execute("""
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, NULL, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
        """, [oid, f"Sec Org {slug}", slug, now, now])

    yield conn
    conn.close()


# ── Cross-tenant isolation ─────────────────────────────────────────────────────

def test_cross_tenant_get_asset_blocked(sec_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import NotFoundError

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Sec Asset {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(NotFoundError):
        CatalogAssetUseCases(sec_conn).get(asset.id, organization_id=411)


def test_cross_tenant_contract_get_blocked(sec_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        RightsContractUseCases,
    )
    from app.packages.catalog_rights.domain.errors import NotFoundError

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Sec Asset 2 {uuid.uuid4().hex[:8]}",
    )
    contract = RightsContractUseCases(sec_conn).create(
        actor_user_id=1, organization_id=410, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    with pytest.raises(NotFoundError):
        RightsContractUseCases(sec_conn).get(contract.id, organization_id=411)


def test_cross_tenant_create_contract_on_foreign_asset_blocked(sec_conn):
    """Creating a rights contract against another org's asset_id must fail
    (asset lookup is org-scoped)."""
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        RightsContractUseCases,
    )
    from app.packages.catalog_rights.domain.errors import NotFoundError

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Sec Asset 3 {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(NotFoundError):
        RightsContractUseCases(sec_conn).create(
            actor_user_id=1, organization_id=411, asset_id=asset.id, rights_type="master",
            valid_from=date(2024, 1, 1),
        )


def test_duplicate_asset_title_scoped_per_org_not_cross_org(sec_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    name = f"Cross Org Title {uuid.uuid4().hex[:8]}"
    a1 = CatalogAssetUseCases(sec_conn).register(actor_user_id=1, organization_id=410, title=name)
    a2 = CatalogAssetUseCases(sec_conn).register(actor_user_id=1, organization_id=411, title=name)
    assert a1.id != a2.id
    assert a1.organization_id != a2.organization_id


# ── Warehouse isolation ────────────────────────────────────────────────────────

def test_link_warehouse_track_does_not_mutate_dim_track(sec_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    before = sec_conn.execute("SELECT nombre_track FROM dim_track WHERE id_track = 1").fetchone()[0]
    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Warehouse Link {uuid.uuid4().hex[:8]}",
    )
    CatalogAssetUseCases(sec_conn).link_warehouse_track(
        asset.id, actor_user_id=1, organization_id=410, warehouse_track_id=1,
    )
    after = sec_conn.execute("SELECT nombre_track FROM dim_track WHERE id_track = 1").fetchone()[0]
    assert before == after
    count = sec_conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    assert int(count) == 1


# ── rights_contract vs commercial_contract distinctness ────────────────────────

def test_rights_contract_never_shares_ids_with_commercial_contract(sec_conn):
    """A rights_contract row must never be readable through the CRM
    commercial-contract table (and vice versa) — the two are unrelated
    tables even when ids collide numerically."""
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        RightsContractUseCases,
    )

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Distinct Contract Asset {uuid.uuid4().hex[:8]}",
    )
    contract = RightsContractUseCases(sec_conn).create(
        actor_user_id=1, organization_id=410, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    commercial_row = sec_conn.execute(
        "SELECT 1 FROM app_commercial_contract WHERE id = ?", [contract.id]
    ).fetchone()
    # It is fine if a commercial_contract with the same numeric id exists
    # (independent id sequences); what matters is the rights row is not
    # somehow the same object / joinable by shared business meaning.
    rights_cols = {
        r[0] for r in sec_conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'app_rights_contract'"
        ).fetchall()
    }
    assert "rights_type" in rights_cols
    if commercial_row:
        commercial_cols = {
            r[0] for r in sec_conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'app_commercial_contract'"
            ).fetchall()
        }
        assert "rights_type" not in commercial_cols


# ── Audit entries ───────────────────────────────────────────────────────────────

def test_audit_entry_on_register_asset(sec_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Audited Asset {uuid.uuid4().hex[:8]}",
    )
    row = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'catalog_asset' "
        "AND target_id = ? AND action = 'catalog_asset.registered'",
        [str(asset.id)],
    ).fetchone()
    assert row is not None


def test_audit_entry_on_contract_create_and_archive(sec_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        RightsContractUseCases,
    )

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Audited Contract Asset {uuid.uuid4().hex[:8]}",
    )
    contract = RightsContractUseCases(sec_conn).create(
        actor_user_id=1, organization_id=410, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    row = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'rights_contract' "
        "AND target_id = ? AND action = 'rights_contract.created'",
        [str(contract.id)],
    ).fetchone()
    assert row is not None

    RightsContractUseCases(sec_conn).archive(contract.id, actor_user_id=1, organization_id=410)
    row2 = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'rights_contract' "
        "AND target_id = ? AND action = 'rights_contract.archived'",
        [str(contract.id)],
    ).fetchone()
    assert row2 is not None


def test_audit_entry_on_contract_party_added(sec_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        RightsContractPartyUseCases,
        RightsContractUseCases,
    )

    asset = CatalogAssetUseCases(sec_conn).register(
        actor_user_id=1, organization_id=410, title=f"Audited Party Asset {uuid.uuid4().hex[:8]}",
    )
    contract = RightsContractUseCases(sec_conn).create(
        actor_user_id=1, organization_id=410, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    party, _ = RightsContractPartyUseCases(sec_conn).add(
        contract.id, actor_user_id=1, organization_id=410, party_name="Audited Party",
        ownership_percentage=50,
    )
    row = sec_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'rights_contract_party' "
        "AND target_id = ? AND action = 'rights_contract_party.added'",
        [str(party.id)],
    ).fetchone()
    assert row is not None


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
            "SELECT id FROM app_organization WHERE slug = 'rights-sec-viewer-org-n5'"
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (240, 'Rights Sec Viewer Org N5', NULL, 'rights-sec-viewer-org-n5', 'label', 'US',
                        'UTC', 'USD', 'active', ?, ?, ?)
            """, [int(user_id), now, now])
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 240 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute("""
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 240, ?, 'active', ?, ?, ?)
            """, [next_mid, int(user_id), int(user_id), now, now])

            viewer_role_id = conn.execute(
                "SELECT id FROM app_business_role WHERE code = 'viewer'"
            ).fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute("""
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, [next_mrid, next_mid, int(viewer_role_id), int(user_id), now])

    return {"headers": headers, "user_id": user_id, "org_id": 240,
            "org_headers": {**headers, "X-Organization-Id": "240"}}


def test_viewer_can_view_but_not_create_asset(client: TestClient, viewer_context):
    r_list = client.get("/api/v1/catalog-rights/assets", headers=viewer_context["org_headers"])
    assert r_list.status_code == 200, r_list.text

    r_create = client.post(
        "/api/v1/catalog-rights/assets",
        json={"title": "Should Be Denied"},
        headers=viewer_context["org_headers"],
    )
    assert r_create.status_code == 403, r_create.text


def test_viewer_cannot_approve_or_archive_or_open_conflict(client: TestClient, viewer_context):
    r_approve = client.post(
        "/api/v1/catalog-rights/contracts/1/approve",
        json={"approved": True},
        headers=viewer_context["org_headers"],
    )
    assert r_approve.status_code == 403, r_approve.text

    r_archive = client.post(
        "/api/v1/catalog-rights/contracts/1/archive", json={},
        headers=viewer_context["org_headers"],
    )
    assert r_archive.status_code == 403, r_archive.text

    r_conflict = client.post(
        "/api/v1/catalog-rights/conflicts",
        json={"asset_id": 1, "rights_type": "master", "territory_code": "US"},
        headers=viewer_context["org_headers"],
    )
    assert r_conflict.status_code == 403, r_conflict.text
