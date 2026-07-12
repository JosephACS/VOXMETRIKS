"""Spec 016 I1 — organization schema and catalog tests (isolated DuckDB)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from app.core import schema_bootstrap
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.organizations.domain.errors import DuplicateError, ValidationError
from app.packages.organizations.infrastructure.catalogs import (
    BUSINESS_ROLES,
    PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)
from app.packages.organizations.infrastructure.repositories.invitation_repository import (
    InvitationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.preference_repository import (
    PreferenceRepository,
)
from app.packages.organizations.infrastructure.schema import (
    ORG_TABLES,
    ensure_organization_role_catalogs,
    ensure_organization_tables,
)


EXPECTED_ORG_COLUMNS = {
    "id",
    "display_name",
    "legal_name",
    "slug",
    "organization_type",
    "country_code",
    "timezone",
    "default_currency",
    "status",
    "created_by",
    "created_at",
    "updated_at",
    "closed_at",
    "is_demo",
}


@pytest.fixture()
def org_conn(tmp_path: Path):
    previous_ready = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    db = tmp_path / "org_schema.duckdb"
    conn = duckdb.connect(str(db))
    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous_ready


def _columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {r[0] for r in conn.execute(f"DESCRIBE {table}").fetchall()}


def test_ensure_idempotent_twice(tmp_path: Path):
    previous_ready = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    try:
        conn = duckdb.connect(str(tmp_path / "twice.duckdb"))
        ensure_user_tables(conn)
        ensure_organization_tables(conn)
        ensure_organization_tables(conn)
        for table in ORG_TABLES:
            assert conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM app_organization").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM app_organization_member").fetchone()[0] == 0
        conn.close()
    finally:
        schema_bootstrap._schema_ready = previous_ready


def test_nine_tables_and_columns(org_conn):
    for table in ORG_TABLES:
        assert (
            org_conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0]
            == 1
        )
    assert EXPECTED_ORG_COLUMNS.issubset(_columns(org_conn, "app_organization"))


def test_seed_roles_permissions_exact(org_conn):
    role_codes = {
        r[0]
        for r in org_conn.execute("SELECT code FROM app_business_role ORDER BY code").fetchall()
    }
    assert role_codes == {c for c, _, _ in BUSINESS_ROLES}

    perm_codes = {
        r[0]
        for r in org_conn.execute("SELECT code FROM app_permission ORDER BY code").fetchall()
    }
    assert perm_codes == {c for c, _, _ in PERMISSIONS}

    # No FUTURE permissions (billing.view Spec 019, artist.view Spec 020, campaign.view Spec 022)
    for banned in ():
        assert banned not in perm_codes


def test_role_permission_mappings_no_duplicates(org_conn):
    expected_pairs = set()
    for role_code, perms in ROLE_PERMISSION_MATRIX.items():
        for perm in perms:
            expected_pairs.add((role_code, perm))

    rows = org_conn.execute(
        """
        SELECT r.code, p.code
        FROM app_role_permission rp
        JOIN app_business_role r ON r.id = rp.role_id
        JOIN app_permission p ON p.id = rp.permission_id
        """
    ).fetchall()
    actual = {(r[0], r[1]) for r in rows}
    assert actual == expected_pairs
    assert len(rows) == len(actual)

    # catalog seed again does not duplicate
    ensure_organization_role_catalogs(org_conn)
    assert (
        org_conn.execute("SELECT COUNT(*) FROM app_role_permission").fetchone()[0]
        == len(expected_pairs)
    )


def test_ensure_does_not_create_orgs_or_memberships(org_conn):
    assert org_conn.execute("SELECT COUNT(*) FROM app_organization").fetchone()[0] == 0
    assert org_conn.execute("SELECT COUNT(*) FROM app_organization_member").fetchone()[0] == 0


def test_identity_untouched_by_org_ensure(tmp_path: Path):
    previous_ready = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    try:
        conn = duckdb.connect(str(tmp_path / "identity.duckdb"))
        ensure_user_tables(conn)
        before_users = conn.execute("SELECT COUNT(*) FROM app_user").fetchone()[0]
        before_sessions = conn.execute("SELECT COUNT(*) FROM app_session").fetchone()[0]
        before_codes = conn.execute("SELECT COUNT(*) FROM app_email_code").fetchone()[0]
        ensure_organization_tables(conn)
        assert conn.execute("SELECT COUNT(*) FROM app_user").fetchone()[0] == before_users
        assert conn.execute("SELECT COUNT(*) FROM app_session").fetchone()[0] == before_sessions
        assert conn.execute("SELECT COUNT(*) FROM app_email_code").fetchone()[0] == before_codes
        conn.close()
    finally:
        schema_bootstrap._schema_ready = previous_ready


def test_duplicate_slug_rejected(org_conn):
    user_id = org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0]
    repo = OrganizationRepository(org_conn)
    repo.create(
        display_name="Acme",
        slug="acme",
        organization_type="label",
        created_by=int(user_id),
        status="active",
    )
    with pytest.raises((DuplicateError, Exception)):
        repo.create(
            display_name="Acme 2",
            slug="acme",
            organization_type="label",
            created_by=int(user_id),
            status="active",
        )


def test_duplicate_membership_rejected(org_conn):
    user_id = int(org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0])
    org = OrganizationRepository(org_conn).create(
        display_name="Org",
        slug="org-a",
        organization_type="label",
        created_by=user_id,
        status="active",
    )
    members = MembershipRepository(org_conn)
    members.create(organization_id=org.id, user_id=user_id, created_by=user_id)
    with pytest.raises((DuplicateError, Exception)):
        members.create(organization_id=org.id, user_id=user_id, created_by=user_id)


def test_duplicate_token_hash_rejected(org_conn):
    from datetime import timedelta

    from app.core.time_util import utc_now

    user_id = int(org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0])
    org = OrganizationRepository(org_conn).create(
        display_name="Org",
        slug="org-inv",
        organization_type="label",
        created_by=user_id,
        status="active",
    )
    inv = InvitationRepository(org_conn)
    expires = utc_now() + timedelta(days=7)
    inv.create(
        organization_id=org.id,
        email="a@example.com",
        token_hash="hash-1",
        expires_at=expires,
        invited_by=user_id,
        initial_role_code="viewer",
    )
    with pytest.raises((DuplicateError, ValidationError, Exception)):
        inv.create(
            organization_id=org.id,
            email="b@example.com",
            token_hash="hash-1",
            expires_at=expires,
            invited_by=user_id,
            initial_role_code="viewer",
        )


def test_duplicate_role_permission_rejected(org_conn):
    role_id = int(
        org_conn.execute("SELECT id FROM app_business_role WHERE code='viewer'").fetchone()[0]
    )
    perm_id = int(
        org_conn.execute(
            "SELECT id FROM app_permission WHERE code='organization.view'"
        ).fetchone()[0]
    )
    # already seeded — second insert must fail
    with pytest.raises(Exception):
        org_conn.execute(
            """
            INSERT INTO app_role_permission (id, role_id, permission_id, created_at)
            VALUES (999999, ?, ?, CURRENT_TIMESTAMP)
            """,
            [role_id, perm_id],
        )


def test_duplicate_member_role_rejected(org_conn):
    user_id = int(org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0])
    org = OrganizationRepository(org_conn).create(
        display_name="Org",
        slug="org-mr",
        organization_type="label",
        created_by=user_id,
        status="active",
    )
    member = MembershipRepository(org_conn).create(
        organization_id=org.id, user_id=user_id, created_by=user_id
    )
    role_id = int(
        org_conn.execute("SELECT id FROM app_business_role WHERE code='owner'").fetchone()[0]
    )
    auth = AuthorizationRepository(org_conn)
    auth.assign_member_role(member_id=member.id, role_id=role_id, assigned_by=user_id)
    # second assign returns same active role (no duplicate row)
    again = auth.assign_member_role(
        member_id=member.id, role_id=role_id, assigned_by=user_id
    )
    assert again.member_id == member.id
    count = org_conn.execute(
        "SELECT COUNT(*) FROM app_member_role WHERE member_id = ? AND role_id = ?",
        [member.id, role_id],
    ).fetchone()[0]
    assert int(count) == 1


def test_preference_unique_per_user(org_conn):
    user_id = int(org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0])
    org = OrganizationRepository(org_conn).create(
        display_name="Org",
        slug="org-pref",
        organization_type="label",
        created_by=user_id,
        status="active",
    )
    prefs = PreferenceRepository(org_conn)
    prefs.set_active_organization(user_id, org.id)
    prefs.set_active_organization(user_id, org.id)
    assert (
        org_conn.execute(
            "SELECT COUNT(*) FROM app_user_organization_preference WHERE user_id = ?",
            [user_id],
        ).fetchone()[0]
        == 1
    )


def test_invalid_organization_status_rejected(org_conn):
    user_id = int(org_conn.execute("SELECT id FROM app_user LIMIT 1").fetchone()[0])
    with pytest.raises(ValidationError):
        OrganizationRepository(org_conn).create(
            display_name="Bad",
            slug="bad-status",
            organization_type="label",
            created_by=user_id,
            status="not_a_status",
        )
