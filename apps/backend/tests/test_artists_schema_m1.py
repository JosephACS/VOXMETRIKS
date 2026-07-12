"""Test M1: Artists schema — Spec 020.

Verifies:
- All 6 artists tables created.
- Natural-key uniqueness ((organization_id, normalized_name) on
  app_artist_profile; (artist_id, system_code) on
  app_artist_external_identifier) is enforced at the application layer
  (see test_artists_use_cases_m2.py) rather than via SQL UNIQUE indexes —
  DuckDB has a known limitation where a secondary index on a column later
  mutated by UPDATE can raise a spurious PRIMARY KEY ConstraintException,
  so these tables intentionally carry no compound UNIQUE constraints.
- status CHECK constraints enforced.
- artist.* permissions seeded in org catalogs.
- dim_artista (warehouse) untouched / not modified by artists schema.
"""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("artists_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)

    # Minimal warehouse table (dim_artista) — analytics domain, not modified by
    # the artists business package. Present so link_warehouse_artist tests work.
    conn.execute("""
        CREATE TABLE dim_artista (
            id_artista     INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
    """)
    conn.execute("INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (1, 'Warehouse Artist')")

    ensure_artist_tables(conn)

    # Restore the global schema-ready flag immediately: it must only be
    # False for the duration of this fixture's own ensure_* calls against
    # its private tmp-path connection, not for the whole test module (other
    # test files sharing the process — e.g. client-based API tests — must
    # see the real value).
    schema_bootstrap._schema_ready = previous

    yield conn
    conn.close()


# ── Table existence ────────────────────────────────────────────────────────────

def test_artist_profile_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_profile LIMIT 0")


def test_artist_organization_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_organization LIMIT 0")


def test_artist_assignment_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_assignment LIMIT 0")


def test_artist_team_member_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_team_member LIMIT 0")


def test_artist_external_identifier_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_external_identifier LIMIT 0")


def test_artist_status_history_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_artist_status_history LIMIT 0")


# ── Idempotent ensure ───────────────────────────────────────────────────────────

def test_ensure_artist_tables_idempotent(db_conn):
    from app.packages.artists.infrastructure.schema import ARTISTS_TABLES, ensure_artist_tables

    ensure_artist_tables(db_conn)
    for table in ARTISTS_TABLES:
        count = db_conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()[0]
        assert int(count) == 1


# ── Natural-key uniqueness (application layer) ─────────────────────────────────
# app_artist_profile.(organization_id, normalized_name) and
# app_artist_external_identifier.(artist_id, system_code) uniqueness is
# enforced by ArtistProfileUseCases.create() / ExternalIdentifierUseCases.set()
# (see test_artists_use_cases_m2.py::test_create_artist_profile_duplicate_raises
# and ::test_set_external_identifier_upsert). No SQL UNIQUE index backs these
# columns — see the module docstring and schema.py for why.


# ── CHECK constraints ──────────────────────────────────────────────────────────

def test_artist_profile_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_artist_profile
                (id, organization_id, display_name, legal_name, normalized_name, status,
                 warehouse_artist_id, created_by, created_at, updated_at)
            VALUES (7001, 1, 'Bad Status', NULL, 'bad status', 'not_a_status', NULL, 1, ?, ?)
        """, [now, now])


def test_artist_assignment_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_artist_assignment
                (id, artist_id, organization_id, user_id, role, status, assigned_at,
                 ended_at, created_at, updated_at)
            VALUES (6001, 1, 1, 1, 'manager', 'invalid_status', ?, NULL, ?, ?)
        """, [now, now, now])


def test_artist_organization_relationship_role_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute("""
            INSERT INTO app_artist_organization
                (id, artist_id, organization_id, relationship_role, is_primary, status,
                 created_at, updated_at)
            VALUES (5001, 1, 1, 'bogus_role', FALSE, 'active', ?, ?)
        """, [now, now])


# ── Permissions seeded ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "code",
    [
        "artist.view",
        "artist.create",
        "artist.update",
        "artist.assign",
        "artist.archive",
        "artist.transfer",
    ],
)
def test_artist_permission_seeded(db_conn, code):
    row = db_conn.execute(
        "SELECT id FROM app_permission WHERE code = ?", [code]
    ).fetchone()
    assert row is not None, f"{code} permission not seeded"


def test_owner_has_artist_transfer(db_conn):
    row = db_conn.execute(
        """
        SELECT 1
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'artist.transfer'
        WHERE br.code = 'owner'
        LIMIT 1
        """
    ).fetchone()
    assert row is not None, "owner role missing artist.transfer"


def test_artist_manager_has_artist_assign(db_conn):
    row = db_conn.execute(
        """
        SELECT 1
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'artist.assign'
        WHERE br.code = 'artist_manager'
        LIMIT 1
        """
    ).fetchone()
    assert row is not None, "artist_manager role missing artist.assign"


def test_viewer_has_only_artist_view(db_conn):
    rows = db_conn.execute(
        """
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'viewer' AND p.domain = 'artist'
        """
    ).fetchall()
    codes = {r[0] for r in rows}
    assert codes == {"artist.view"}


# ── Warehouse (dim_artista) untouched ──────────────────────────────────────────

def test_dim_artista_untouched_by_artist_schema(db_conn):
    """Artists schema addition must not modify the analytics warehouse table."""
    cols = {
        r[0] for r in db_conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_artista'"
        ).fetchall()
    }
    assert cols == {"id_artista", "nombre_artista"}
    count = db_conn.execute("SELECT COUNT(*) FROM dim_artista").fetchone()[0]
    assert int(count) == 1


def test_billing_tables_still_present(db_conn):
    """Artists schema addition must not break billing tables."""
    db_conn.execute("SELECT id FROM app_billing_profile LIMIT 0")
    db_conn.execute("SELECT id FROM app_invoice LIMIT 0")
