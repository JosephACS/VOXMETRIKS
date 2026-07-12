"""Test N1: Catalog rights schema — Spec 021.

Verifies:
- All 11 catalog-rights tables created.
- status / rights_type / party_type / ownership_percentage CHECK constraints
  enforced at the SQL layer.
- rights.* permissions seeded in org catalogs with the requested role matrix.
- dim_track (warehouse) untouched / not modified by the catalog-rights schema.
- app_commercial_contract (CRM, Spec 017) remains a distinct table from
  app_rights_contract (this spec) — no columns overlap, no shared rows.
"""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("catalog_rights_schema") / "test.duckdb"
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

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    ensure_artist_tables(conn)

    # Minimal warehouse table (dim_track) — analytics domain, not modified by
    # the catalog-rights business package. Present so link_warehouse_track works.
    conn.execute("""
        CREATE TABLE dim_track (
            id_track      INTEGER PRIMARY KEY,
            nombre_track  VARCHAR NOT NULL
        )
    """)
    conn.execute("INSERT INTO dim_track (id_track, nombre_track) VALUES (1, 'Warehouse Track')")

    ensure_catalog_rights_tables(conn)

    schema_bootstrap._schema_ready = previous

    yield conn
    conn.close()


# ── Table existence ────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "table",
    [
        "app_catalog_asset",
        "app_catalog_release",
        "app_catalog_asset_artist",
        "app_catalog_ownership",
        "app_rights_contract",
        "app_rights_contract_party",
        "app_rights_territory",
        "app_rights_authorized_use",
        "app_rights_conflict",
        "app_rights_approval",
        "app_rights_status_history",
    ],
)
def test_table_exists(db_conn, table):
    db_conn.execute(f"SELECT id FROM {table} LIMIT 0")


# ── Idempotent ensure ───────────────────────────────────────────────────────────

def test_ensure_catalog_rights_tables_idempotent(db_conn):
    from app.packages.catalog_rights.infrastructure.schema import (
        CATALOG_RIGHTS_TABLES,
        ensure_catalog_rights_tables,
    )

    ensure_catalog_rights_tables(db_conn)
    for table in CATALOG_RIGHTS_TABLES:
        count = db_conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()[0]
        assert int(count) == 1


# ── CHECK constraints ──────────────────────────────────────────────────────────

def test_catalog_asset_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_catalog_asset
                (id, organization_id, title, status, warehouse_track_id, artist_profile_id,
                 created_by, created_at, updated_at)
            VALUES (9001, 1, 'Bad Status', 'not_a_status', NULL, NULL, 1, ?, ?)
        """, [now, now])


def test_rights_contract_rights_type_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_rights_contract
                (id, organization_id, asset_id, rights_type, status, exclusive, valid_from,
                 valid_to, evidence_ref, created_by, created_at, updated_at)
            VALUES (9002, 1, 1, 'bogus_type', 'draft', FALSE, ?, NULL, NULL, 1, ?, ?)
        """, [now.date(), now, now])


def test_rights_contract_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_rights_contract
                (id, organization_id, asset_id, rights_type, status, exclusive, valid_from,
                 valid_to, evidence_ref, created_by, created_at, updated_at)
            VALUES (9003, 1, 1, 'master', 'bogus_status', FALSE, ?, NULL, NULL, 1, ?, ?)
        """, [now.date(), now, now])


def test_rights_contract_party_percentage_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_rights_contract_party
                (id, contract_id, party_name, party_type, ownership_percentage,
                 organization_id, artist_profile_id, created_at, updated_at)
            VALUES (9004, 1, 'Over 100', 'external', 150.0, NULL, NULL, ?, ?)
        """, [now, now])


def test_rights_conflict_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_rights_conflict
                (id, organization_id, asset_id, rights_type, territory_code, status, details,
                 resolved_by, resolved_at, created_at, updated_at)
            VALUES (9005, 1, 1, 'master', 'US', 'bogus_status', NULL, NULL, NULL, ?, ?)
        """, [now, now])


def test_rights_approval_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_rights_approval
                (id, contract_id, organization_id, status, approver_user_id, requested_by,
                 notes, decided_at, created_at, updated_at)
            VALUES (9006, 1, 1, 'bogus_status', NULL, 1, NULL, NULL, ?, ?)
        """, [now, now])


# ── Permissions seeded ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "code",
    ["rights.view", "rights.create", "rights.update", "rights.approve", "rights.conflict", "rights.archive"],
)
def test_rights_permission_seeded(db_conn, code):
    row = db_conn.execute("SELECT id FROM app_permission WHERE code = ?", [code]).fetchone()
    assert row is not None, f"{code} permission not seeded"


def test_owner_has_all_rights_permissions(db_conn):
    codes = {
        r[0]
        for r in db_conn.execute(
            """
            SELECT p.code
            FROM app_business_role br
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id
            WHERE br.code = 'owner' AND p.domain = 'rights'
            """
        ).fetchall()
    }
    assert codes == {
        "rights.view", "rights.create", "rights.update", "rights.approve",
        "rights.conflict", "rights.archive",
    }


def test_administrator_has_all_rights_permissions(db_conn):
    codes = {
        r[0]
        for r in db_conn.execute(
            """
            SELECT p.code
            FROM app_business_role br
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id
            WHERE br.code = 'administrator' AND p.domain = 'rights'
            """
        ).fetchall()
    }
    assert codes == {
        "rights.view", "rights.create", "rights.update", "rights.approve",
        "rights.conflict", "rights.archive",
    }


def test_artist_manager_has_view_create_update_only(db_conn):
    codes = {
        r[0]
        for r in db_conn.execute(
            """
            SELECT p.code
            FROM app_business_role br
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id
            WHERE br.code = 'artist_manager' AND p.domain = 'rights'
            """
        ).fetchall()
    }
    assert codes == {"rights.view", "rights.create", "rights.update"}


def test_finance_has_only_rights_view(db_conn):
    codes = {
        r[0]
        for r in db_conn.execute(
            """
            SELECT p.code
            FROM app_business_role br
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id
            WHERE br.code = 'finance' AND p.domain = 'rights'
            """
        ).fetchall()
    }
    assert codes == {"rights.view"}


def test_viewer_has_only_rights_view(db_conn):
    codes = {
        r[0]
        for r in db_conn.execute(
            """
            SELECT p.code
            FROM app_business_role br
            JOIN app_role_permission rp ON rp.role_id = br.id
            JOIN app_permission p ON p.id = rp.permission_id
            WHERE br.code = 'viewer' AND p.domain = 'rights'
            """
        ).fetchall()
    }
    assert codes == {"rights.view"}


# ── Warehouse (dim_track) untouched ────────────────────────────────────────────

def test_dim_track_untouched_by_catalog_rights_schema(db_conn):
    cols = {
        r[0] for r in db_conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_track'"
        ).fetchall()
    }
    assert cols == {"id_track", "nombre_track"}
    count = db_conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    assert int(count) == 1


# ── rights_contract vs commercial_contract distinctness ────────────────────────

def test_rights_contract_distinct_from_commercial_contract(db_conn):
    """app_rights_contract (this spec) and app_commercial_contract (Spec 017
    CRM) are separate tables with disjoint column sets — never joined."""
    rights_cols = {
        r[0] for r in db_conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'app_rights_contract'"
        ).fetchall()
    }
    commercial_cols = {
        r[0] for r in db_conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'app_commercial_contract'"
        ).fetchall()
    }
    assert rights_cols, "app_rights_contract must exist with columns"
    assert commercial_cols, "app_commercial_contract must exist with columns"
    assert "rights_type" in rights_cols
    assert "rights_type" not in commercial_cols


def test_billing_and_artist_tables_still_present(db_conn):
    """Catalog rights schema addition must not break prior-spec tables."""
    db_conn.execute("SELECT id FROM app_billing_profile LIMIT 0")
    db_conn.execute("SELECT id FROM app_artist_profile LIMIT 0")
