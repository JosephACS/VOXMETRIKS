"""Spec 051 — approval atomicity: compensate only what THIS call created.

Uses a throwaway DuckDB under ``tmp_path``; the canonical warehouse is never opened.
"""

from __future__ import annotations

import duckdb
import pytest

from app.packages.artists.identity_access import ARTIST_WORKSPACE_TYPE
from app.packages.artists.identity_access.use_cases import (
    ArtistAccessRequestUseCases,
    PlatformArtistRequestUseCases,
    _create_membership,
    _create_profile,
    _set_request_status,
)
from app.packages.artists.identity_access.workspace_provisioning import (
    WorkspaceProvisionResult,
    provision_artist_workspace,
)

ADMIN = 52001
CLAIMER = 52002
WAREHOUSE_FREE = 5201


@pytest.fixture()
def db(tmp_path, monkeypatch):
    from app.core import schema_bootstrap
    from app.core.time_util import utc_now
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_publishing.infrastructure.schema import (
        ensure_catalog_publishing_tables,
    )
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables

    monkeypatch.setenv("VOXMETRIKS_TEST_ISOLATION", "1")
    monkeypatch.chdir(tmp_path)

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "spec051_atomicity.duckdb"))

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_publishing_tables(conn)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_artista (
            id_artista     INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (?, ?)",
        [WAREHOUSE_FREE, "Atomic Artist 051"],
    )

    now = utc_now()
    for uid, uname, role in (
        (ADMIN, "spec051_atomic_admin", "admin"),
        (CLAIMER, "spec051_atomic_claimer", "user"),
    ):
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre,
                 created_at, preferences_json, email_verified, auth_provider)
            VALUES (?, ?, ?, ?, ?, 'Free', NULL, ?, '{}', TRUE, 'local')
            """,
            [uid, uname, f"{uname}@test.local", hash_password("pass"), role, now],
        )

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


def _create_new(conn, *, user_id=CLAIMER, name="Brand New Atomic Act"):
    return ArtistAccessRequestUseCases(conn).create(
        user_id=user_id,
        request_type="create_new",
        proposed_display_name=name,
        relationship_type="artist_self",
        accuracy_attested=True,
    )


def _claim(conn, *, user_id=CLAIMER, warehouse_artist_id=WAREHOUSE_FREE):
    return ArtistAccessRequestUseCases(conn).create(
        user_id=user_id,
        request_type="claim_ownership",
        warehouse_artist_id=warehouse_artist_id,
        relationship_type="artist_self",
        evidence_url="https://evidence.test/atomic-claim",
    )


def _approve(conn, request_id: int):
    return PlatformArtistRequestUseCases(conn).approve(
        user_id=ADMIN, request_id=request_id
    )


def _baseline(conn) -> dict[str, int]:
    return {
        "workspaces": int(
            conn.execute(
                "SELECT COUNT(*) FROM app_organization WHERE organization_type = ?",
                [ARTIST_WORKSPACE_TYPE],
            ).fetchone()[0]
        ),
        "org_members": int(
            conn.execute("SELECT COUNT(*) FROM app_organization_member").fetchone()[0]
        ),
        "member_roles": int(
            conn.execute("SELECT COUNT(*) FROM app_member_role").fetchone()[0]
        ),
        "profiles": int(
            conn.execute("SELECT COUNT(*) FROM app_artist_profile").fetchone()[0]
        ),
        "artist_memberships": int(
            conn.execute("SELECT COUNT(*) FROM app_artist_membership").fetchone()[0]
        ),
    }


def _assert_at_baseline(conn, baseline: dict[str, int], *, request_id: int) -> None:
    assert _baseline(conn) == baseline
    status = conn.execute(
        "SELECT status FROM app_artist_access_request WHERE id = ?", [request_id]
    ).fetchone()
    assert status is not None and status[0] == "pending"


def _assert_single_owner_workspace(conn, *, owner_user_id: int) -> None:
    workspaces = int(
        conn.execute(
            "SELECT COUNT(*) FROM app_organization WHERE organization_type = ?",
            [ARTIST_WORKSPACE_TYPE],
        ).fetchone()[0]
    )
    assert workspaces == 1
    owners = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM app_artist_membership
            WHERE user_id = ? AND role = 'owner' AND status = 'active'
            """,
            [owner_user_id],
        ).fetchone()[0]
    )
    assert owners == 1
    org_owners = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM app_organization_member m
            INNER JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
            INNER JOIN app_business_role r ON r.id = mr.role_id AND r.code = 'owner'
            INNER JOIN app_organization o
                ON o.id = m.organization_id AND o.organization_type = ?
            WHERE m.user_id = ? AND m.status = 'active'
            """,
            [ARTIST_WORKSPACE_TYPE, owner_user_id],
        ).fetchone()[0]
    )
    assert org_owners == 1


# ── create_new path: failure after each stage ──────────────────────────────


def test_create_new_compensates_after_workspace_org_insert(db, monkeypatch):
    req = _create_new(db)
    baseline = _baseline(db)

    import app.packages.artists.identity_access.workspace_provisioning as wp

    real_ensure = wp._ensure_owner_membership

    def _boom(*_a, **_k):
        raise RuntimeError("injected: after workspace create")

    monkeypatch.setattr(wp, "_ensure_owner_membership", _boom)

    with pytest.raises(Exception):
        _approve(db, req["id"])

    # Restore so retries / later assertions use the real ensure.
    monkeypatch.setattr(wp, "_ensure_owner_membership", real_ensure)
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


def test_create_new_compensates_after_org_owner_membership(db, monkeypatch):
    req = _create_new(db)
    baseline = _baseline(db)

    real_create = _create_profile

    def _boom(*_a, **_k):
        raise RuntimeError("injected: after org owner membership")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_profile",
        _boom,
    )
    with pytest.raises(RuntimeError, match="after org owner membership"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_profile",
        real_create,
    )
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


def test_create_new_compensates_after_profile_create(db, monkeypatch):
    req = _create_new(db)
    baseline = _baseline(db)

    real_membership = _create_membership

    def _boom(*_a, **_k):
        raise RuntimeError("injected: after profile create")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        _boom,
    )
    with pytest.raises(RuntimeError, match="after profile create"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        real_membership,
    )
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


def test_create_new_compensates_after_artist_membership(db, monkeypatch):
    req = _create_new(db)
    baseline = _baseline(db)

    real_status = _set_request_status

    def _boom(*_a, **_k):
        raise RuntimeError("injected: after artist membership")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        _boom,
    )
    with pytest.raises(RuntimeError, match="after artist membership"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        real_status,
    )
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


def test_create_new_compensates_after_request_status_write(db, monkeypatch):
    req = _create_new(db)
    baseline = _baseline(db)

    real_status = _set_request_status

    def _write_then_boom(conn, request_id, **kwargs):
        real_status(conn, request_id, **kwargs)
        raise RuntimeError("injected: after request status write")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        _write_then_boom,
    )
    with pytest.raises(RuntimeError, match="after request status write"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        real_status,
    )
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


# ── claim_ownership path (happy compensation + retry) ──────────────────────


def test_claim_compensates_after_profile_create_and_retries_once(db, monkeypatch):
    req = _claim(db)
    baseline = _baseline(db)

    real_membership = _create_membership

    def _boom(*_a, **_k):
        raise RuntimeError("injected: claim after profile")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        _boom,
    )
    with pytest.raises(RuntimeError, match="claim after profile"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        real_membership,
    )
    _assert_at_baseline(db, baseline, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


# ── create vs reuse compensation boundary ──────────────────────────────────


def test_compensate_does_not_delete_reused_workspace(db):
    """Reuse path: created_organization=False must leave the preexisting org."""
    first = provision_artist_workspace(
        db,
        display_name="Reusable Workspace",
        owner_user_id=CLAIMER,
        seed_key="request:reuse-guard",
    )
    assert first.created_organization is True

    second = provision_artist_workspace(
        db,
        display_name="Reusable Workspace",
        owner_user_id=CLAIMER,
        seed_key="request:reuse-guard",
    )
    assert isinstance(second, WorkspaceProvisionResult)
    assert second.organization_id == first.organization_id
    assert second.created_organization is False
    assert second.created_membership_id is None
    assert second.created_role_assignment is False

    from app.packages.artists.identity_access.workspace_provisioning import (
        compensate_created_workspace,
    )

    compensate_created_workspace(
        db,
        organization_id=second.organization_id,
        created_organization=second.created_organization,
        created_membership_id=second.created_membership_id,
        created_role_assignment=second.created_role_assignment,
        created_member_role_id=second.created_member_role_id,
    )
    still = db.execute(
        "SELECT COUNT(*) FROM app_organization WHERE id = ?",
        [first.organization_id],
    ).fetchone()[0]
    assert int(still) == 1


# ── REUSE path: mutate preexisting rows, compensate snapshots, retry once ──


def _logical_membership(conn, membership_id: int) -> dict:
    cols = (
        "id",
        "organization_id",
        "user_id",
        "status",
        "joined_at",
        "suspended_at",
        "left_at",
        "removed_at",
        "created_by",
        "created_at",
        "updated_at",
    )
    row = conn.execute(
        f"SELECT {', '.join(cols)} FROM app_organization_member WHERE id = ?",
        [membership_id],
    ).fetchone()
    assert row is not None
    return dict(zip(cols, row))


def _logical_member_role(conn, role_row_id: int) -> dict:
    cols = (
        "id",
        "member_id",
        "role_id",
        "status",
        "assigned_by",
        "assigned_at",
        "revoked_by",
        "revoked_at",
    )
    row = conn.execute(
        f"SELECT {', '.join(cols)} FROM app_member_role WHERE id = ?",
        [role_row_id],
    ).fetchone()
    assert row is not None
    return dict(zip(cols, row))


def _logical_profile(conn, profile_id: int) -> dict:
    from app.packages.artists.identity_access.use_cases import _get_profile

    return _get_profile(conn, profile_id)


def _seed_zero_profile_with_workspace(conn, *, display_name: str, membership_status: str):
    """Preexisting workspace + suspended/left membership + revoked owner role + org_id=0 profile."""
    from app.core.time_util import utc_now
    from app.packages.organizations.domain.enums import MemberRoleStatus
    from app.packages.organizations.infrastructure.repositories.authorization_repository import (
        AuthorizationRepository,
    )

    profile = _create_profile(
        conn,
        display_name=display_name,
        organization_id=0,
        warehouse_artist_id=None,
        created_by=CLAIMER,
    )
    profile_id = int(profile["id"])
    ws = provision_artist_workspace(
        conn,
        display_name=display_name,
        owner_user_id=CLAIMER,
        seed_key=f"profile:{profile_id}",
    )
    assert ws.created_organization is True
    membership_id = int(
        conn.execute(
            """
            SELECT id FROM app_organization_member
            WHERE organization_id = ? AND user_id = ?
            """,
            [ws.organization_id, CLAIMER],
        ).fetchone()[0]
    )
    owner_role_id = AuthorizationRepository(conn).get_role_id_by_code("owner")
    role_row_id = int(
        conn.execute(
            """
            SELECT id FROM app_member_role
            WHERE member_id = ? AND role_id = ?
            """,
            [membership_id, owner_role_id],
        ).fetchone()[0]
    )

    now = utc_now()
    if membership_status == "suspended":
        conn.execute(
            """
            UPDATE app_organization_member
            SET status = 'suspended', suspended_at = ?, left_at = NULL, removed_at = NULL, updated_at = ?
            WHERE id = ?
            """,
            [now, now, membership_id],
        )
    elif membership_status == "left":
        conn.execute(
            """
            UPDATE app_organization_member
            SET status = 'left', suspended_at = NULL, left_at = ?, removed_at = NULL, updated_at = ?
            WHERE id = ?
            """,
            [now, now, membership_id],
        )
    else:
        raise AssertionError(f"unsupported membership_status={membership_status}")

    conn.execute(
        """
        UPDATE app_member_role
        SET status = ?, revoked_by = ?, revoked_at = ?
        WHERE id = ?
        """,
        [MemberRoleStatus.REVOKED.value, CLAIMER, now, role_row_id],
    )

    return {
        "workspace_id": ws.organization_id,
        "membership_id": membership_id,
        "role_row_id": role_row_id,
        "profile_id": profile_id,
        "display_name": display_name,
    }


def test_reuse_restores_suspended_membership_and_revoked_role(db, monkeypatch):
    from app.packages.artists.application.use_cases import _update_profile_row

    seeded = _seed_zero_profile_with_workspace(
        db, display_name="Reuse Suspended Act", membership_status="suspended"
    )
    _update_profile_row(db, seeded["profile_id"], warehouse_artist_id=WAREHOUSE_FREE)
    req = _claim(db)

    before_membership = _logical_membership(db, seeded["membership_id"])
    before_role = _logical_member_role(db, seeded["role_row_id"])
    before_profile = _logical_profile(db, seeded["profile_id"])
    baseline_counts = _baseline(db)
    assert before_membership["status"] == "suspended"
    assert before_role["status"] == "revoked"
    assert before_profile["organization_id"] == 0

    real_membership = _create_membership

    def _boom(*_a, **_k):
        raise RuntimeError("injected: after reuse profile mutate")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        _boom,
    )
    with pytest.raises(RuntimeError, match="after reuse profile mutate"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._create_membership",
        real_membership,
    )

    assert _logical_membership(db, seeded["membership_id"]) == before_membership
    assert _logical_member_role(db, seeded["role_row_id"]) == before_role
    after_profile = _logical_profile(db, seeded["profile_id"])
    assert after_profile["organization_id"] == before_profile["organization_id"]
    assert after_profile["warehouse_artist_id"] == before_profile["warehouse_artist_id"]
    assert after_profile["updated_at"] == before_profile["updated_at"]
    _assert_at_baseline(db, baseline_counts, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)
    assert _logical_membership(db, seeded["membership_id"])["status"] == "active"
    assert _logical_member_role(db, seeded["role_row_id"])["status"] == "active"
    final_profile = _logical_profile(db, seeded["profile_id"])
    assert final_profile["organization_id"] == seeded["workspace_id"]
    assert final_profile["warehouse_artist_id"] == WAREHOUSE_FREE


def test_reuse_left_membership_restored_after_role_reactivation_failure(db, monkeypatch):
    from app.packages.artists.application.use_cases import _update_profile_row
    import app.packages.organizations.infrastructure.repositories.authorization_repository as auth_mod

    seeded = _seed_zero_profile_with_workspace(
        db, display_name="Reuse Left Act", membership_status="left"
    )
    _update_profile_row(db, seeded["profile_id"], warehouse_artist_id=WAREHOUSE_FREE)
    req = _claim(db)

    before_membership = _logical_membership(db, seeded["membership_id"])
    before_role = _logical_member_role(db, seeded["role_row_id"])
    before_profile = _logical_profile(db, seeded["profile_id"])
    baseline_counts = _baseline(db)
    assert before_membership["status"] == "left"

    real_assign = auth_mod.AuthorizationRepository.assign_member_role

    def _assign_then_boom(self, *args, **kwargs):
        result = real_assign(self, *args, **kwargs)
        raise RuntimeError("injected: after owner role reactivation")

    monkeypatch.setattr(
        auth_mod.AuthorizationRepository,
        "assign_member_role",
        _assign_then_boom,
    )
    with pytest.raises(Exception):
        _approve(db, req["id"])

    monkeypatch.setattr(
        auth_mod.AuthorizationRepository,
        "assign_member_role",
        real_assign,
    )

    assert _logical_membership(db, seeded["membership_id"]) == before_membership
    assert _logical_member_role(db, seeded["role_row_id"]) == before_role
    restored_profile = _logical_profile(db, seeded["profile_id"])
    assert restored_profile["organization_id"] == before_profile["organization_id"]
    assert restored_profile["warehouse_artist_id"] == before_profile["warehouse_artist_id"]
    assert restored_profile["updated_at"] == before_profile["updated_at"]
    _assert_at_baseline(db, baseline_counts, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)


def test_reuse_profile_org0_restored_after_status_write_failure(db, monkeypatch):
    from app.packages.artists.application.use_cases import _update_profile_row

    seeded = _seed_zero_profile_with_workspace(
        db, display_name="Reuse Status Act", membership_status="suspended"
    )
    _update_profile_row(db, seeded["profile_id"], warehouse_artist_id=WAREHOUSE_FREE)
    req = _claim(db)
    before_membership = _logical_membership(db, seeded["membership_id"])
    before_role = _logical_member_role(db, seeded["role_row_id"])
    before_profile = _logical_profile(db, seeded["profile_id"])
    baseline_counts = _baseline(db)

    real_status = _set_request_status

    def _write_then_boom(conn, request_id, **kwargs):
        real_status(conn, request_id, **kwargs)
        raise RuntimeError("injected: after reuse status write")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        _write_then_boom,
    )
    with pytest.raises(RuntimeError, match="after reuse status write"):
        _approve(db, req["id"])

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases._set_request_status",
        real_status,
    )

    assert _logical_membership(db, seeded["membership_id"]) == before_membership
    assert _logical_member_role(db, seeded["role_row_id"]) == before_role
    restored_profile = _logical_profile(db, seeded["profile_id"])
    assert restored_profile["organization_id"] == before_profile["organization_id"] == 0
    assert restored_profile["warehouse_artist_id"] == before_profile["warehouse_artist_id"]
    assert restored_profile["updated_at"] == before_profile["updated_at"]
    _assert_at_baseline(db, baseline_counts, request_id=req["id"])

    result = _approve(db, req["id"])
    assert result["status"] == "approved"
    _assert_single_owner_workspace(db, owner_user_id=CLAIMER)
    workspaces = int(
        db.execute(
            "SELECT COUNT(*) FROM app_organization WHERE organization_type = ?",
            [ARTIST_WORKSPACE_TYPE],
        ).fetchone()[0]
    )
    assert workspaces == 1
