"""Spec 051 T002 — discovery, evidence, workspace provisioning and migration.

Everything runs against a throwaway DuckDB under ``tmp_path``; the canonical
warehouse is never opened.
"""

from __future__ import annotations

import duckdb
import pytest

from app.packages.artists.identity_access import (
    ARTIST_WORKSPACE_TYPE,
    INDEPENDENT_ORG_ID,
    permissions_for_role,
)
from app.packages.artists.identity_access.errors import (
    ConflictError,
    EvidenceRequired,
    ValidationError,
)
from app.packages.artists.identity_access.use_cases import (
    ArtistAccessRequestUseCases,
    ArtistSpaceUseCases,
    PlatformArtistRequestUseCases,
)
from app.packages.artists.identity_access.workspace_provisioning import (
    WorkspaceProvisionError,
    migrate_zero_backed_profile,
    provision_artist_workspace,
    workspace_slug,
)

ADMIN = 51001
CLAIMER = 51002
OTHER = 51003

WAREHOUSE_FREE = 5101
WAREHOUSE_MANAGED = 5102


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
    conn = duckdb.connect(str(tmp_path / "spec051_contracts.duckdb"))

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
        "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (?, ?), (?, ?)",
        [WAREHOUSE_FREE, "Free Artist 051", WAREHOUSE_MANAGED, "Managed Artist 051"],
    )

    now = utc_now()
    for uid, uname, role in (
        (ADMIN, "spec051_admin", "admin"),
        (CLAIMER, "spec051_claimer", "user"),
        (OTHER, "spec051_other", "user"),
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


def _claim(conn, *, user_id=CLAIMER, warehouse_artist_id=WAREHOUSE_FREE, **overrides):
    payload = {
        "user_id": user_id,
        "request_type": "claim_ownership",
        "warehouse_artist_id": warehouse_artist_id,
        "relationship_type": "artist_self",
        "evidence_url": "https://evidence.test/proof",
    }
    payload.update(overrides)
    return ArtistAccessRequestUseCases(conn).create(**payload)


def _approve(conn, request_id: int) -> dict:
    return PlatformArtistRequestUseCases(conn).approve(
        user_id=ADMIN, request_id=request_id
    )


# ── additive schema ────────────────────────────────────────────────────────


def test_additive_columns_exist(db):
    profile_cols = {r[0] for r in db.execute("DESCRIBE app_artist_profile").fetchall()}
    assert {"bio", "country_code", "primary_genre", "website_url", "image_url"} <= profile_cols
    request_cols = {
        r[0] for r in db.execute("DESCRIBE app_artist_access_request").fetchall()
    }
    assert {"relationship_type", "evidence_url", "evidence_note"} <= request_cols


def test_additive_columns_are_idempotent(db):
    from app.packages.artists.infrastructure.schema import _apply_artist_additive_columns

    before = db.execute("DESCRIBE app_artist_profile").fetchall()
    _apply_artist_additive_columns(db)
    _apply_artist_additive_columns(db)
    assert db.execute("DESCRIBE app_artist_profile").fetchall() == before


# ── evidence validation ────────────────────────────────────────────────────


def test_claim_requires_relationship_and_evidence(db):
    uc = ArtistAccessRequestUseCases(db)
    with pytest.raises(EvidenceRequired):
        uc.create(
            user_id=CLAIMER,
            request_type="claim_ownership",
            warehouse_artist_id=WAREHOUSE_FREE,
        )
    with pytest.raises(EvidenceRequired):
        uc.create(
            user_id=CLAIMER,
            request_type="claim_ownership",
            warehouse_artist_id=WAREHOUSE_FREE,
            relationship_type="manager",
        )


def test_claim_rejects_unknown_relationship_and_bad_url(db):
    uc = ArtistAccessRequestUseCases(db)
    with pytest.raises(ValidationError):
        uc.create(
            user_id=CLAIMER,
            request_type="claim_ownership",
            warehouse_artist_id=WAREHOUSE_FREE,
            relationship_type="best_friend",
            evidence_note="trust me",
        )
    with pytest.raises(ValidationError):
        uc.create(
            user_id=CLAIMER,
            request_type="claim_ownership",
            warehouse_artist_id=WAREHOUSE_FREE,
            relationship_type="manager",
            evidence_url="javascript:alert(1)",
        )


def test_claim_persists_evidence(db):
    req = _claim(db, evidence_note="Verified label contract")
    assert req["relationship_type"] == "artist_self"
    assert req["evidence_url"] == "https://evidence.test/proof"
    assert req["evidence_note"] == "Verified label contract"
    assert ArtistAccessRequestUseCases(db).list_mine(CLAIMER)[0]["evidence_url"] == (
        "https://evidence.test/proof"
    )


def test_create_new_requires_relationship_and_attestation(db):
    uc = ArtistAccessRequestUseCases(db)
    with pytest.raises(EvidenceRequired):
        uc.create(
            user_id=CLAIMER,
            request_type="create_new",
            proposed_display_name="Brand New Act",
            relationship_type="artist_self",
        )
    with pytest.raises(EvidenceRequired):
        uc.create(
            user_id=CLAIMER,
            request_type="create_new",
            proposed_display_name="Brand New Act",
            accuracy_attested=True,
        )
    created = uc.create(
        user_id=CLAIMER,
        request_type="create_new",
        proposed_display_name="Brand New Act",
        relationship_type="artist_self",
        accuracy_attested=True,
    )
    assert created["status"] == "pending"


def test_request_access_needs_managed_target_and_non_owner_role(db):
    uc = ArtistAccessRequestUseCases(db)
    with pytest.raises(Exception):
        # No profile exists for this warehouse artist yet.
        uc.create(
            user_id=OTHER,
            request_type="request_access",
            warehouse_artist_id=WAREHOUSE_MANAGED,
        )
    approved = _approve(db, _claim(db, warehouse_artist_id=WAREHOUSE_MANAGED)["id"])
    profile_id = approved["profile"]["id"]
    with pytest.raises(ValidationError):
        uc.create(
            user_id=OTHER,
            request_type="request_access",
            target_artist_profile_id=profile_id,
            proposed_role="owner",
        )
    ok = uc.create(
        user_id=OTHER,
        request_type="request_access",
        target_artist_profile_id=profile_id,
        proposed_role="member",
    )
    assert ok["proposed_role"] == "member"


# ── workspace provisioning ─────────────────────────────────────────────────


def test_approve_provisions_hidden_workspace(db):
    result = _approve(db, _claim(db)["id"])
    profile = result["profile"]
    assert profile["organization_id"] != INDEPENDENT_ORG_ID

    org = db.execute(
        "SELECT organization_type, slug, status FROM app_organization WHERE id = ?",
        [profile["organization_id"]],
    ).fetchone()
    assert org[0] == ARTIST_WORKSPACE_TYPE
    assert org[1] == workspace_slug(f"warehouse:{WAREHOUSE_FREE}")
    assert org[2] == "active"

    owner_membership = db.execute(
        """
        SELECT COUNT(*)
        FROM app_organization_member m
        INNER JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
        INNER JOIN app_business_role r ON r.id = mr.role_id AND r.code = 'owner'
        WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
        """,
        [profile["organization_id"], CLAIMER],
    ).fetchone()[0]
    assert int(owner_membership) == 1
    assert result["membership"]["role"] == "owner"
    assert result["reviewer_became_member"] is False


def test_provisioning_is_idempotent_for_the_same_seed(db):
    first = provision_artist_workspace(
        db, display_name="Same Artist", owner_user_id=CLAIMER, seed_key="profile:777"
    )
    second = provision_artist_workspace(
        db, display_name="Same Artist", owner_user_id=CLAIMER, seed_key="profile:777"
    )
    assert first.organization_id == second.organization_id
    assert first.created_organization is True
    assert second.created_organization is False
    assert second.created_membership_id is None
    assert second.created_role_assignment is False
    members = db.execute(
        "SELECT COUNT(*) FROM app_organization_member WHERE organization_id = ?",
        [first.organization_id],
    ).fetchone()[0]
    assert int(members) == 1


def test_provisioning_refuses_to_hijack_a_product_organization(db):
    from app.packages.organizations.infrastructure.repositories.organization_repository import (
        OrganizationRepository,
    )

    slug = workspace_slug("profile:999")
    OrganizationRepository(db).create(
        display_name="Real Label",
        slug=slug,
        organization_type="label",
        created_by=ADMIN,
        status="active",
    )
    with pytest.raises(WorkspaceProvisionError):
        provision_artist_workspace(
            db, display_name="Real Label", owner_user_id=CLAIMER, seed_key="profile:999"
        )


def test_hidden_workspace_is_not_an_organization_space(db):
    from app.packages.organizations.infrastructure.repositories.organization_repository import (
        OrganizationRepository,
    )

    result = _approve(db, _claim(db)["id"])
    workspace_id = result["profile"]["organization_id"]
    listed = {o.id for o in OrganizationRepository(db).list_for_user(CLAIMER)}
    assert workspace_id not in listed


# ── rollback ───────────────────────────────────────────────────────────────


def test_approve_rolls_back_when_provisioning_fails(db, monkeypatch):
    request_id = _claim(db)["id"]

    def _boom(*_args, **_kwargs):
        raise RuntimeError("owner role catalog unavailable")

    monkeypatch.setattr(
        "app.packages.artists.identity_access.use_cases.provision_artist_workspace",
        _boom,
    )
    with pytest.raises(WorkspaceProvisionError) as exc:
        _approve(db, request_id)
    assert exc.value.code == "artist_workspace_provision_failed"

    still_pending = ArtistAccessRequestUseCases(db).list_mine(CLAIMER)[0]
    assert still_pending["status"] == "pending"
    assert (
        int(db.execute("SELECT COUNT(*) FROM app_artist_profile").fetchone()[0]) == 0
    )
    assert (
        int(db.execute("SELECT COUNT(*) FROM app_artist_membership").fetchone()[0]) == 0
    )


# ── legacy migration ───────────────────────────────────────────────────────


def _legacy_profile(conn, *, profile_id: int, owner_user_id: int) -> None:
    from app.core.time_util import utc_now

    now = utc_now()
    conn.execute(
        """
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name,
             status, warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (?, 0, 'Legacy Artist', NULL, 'legacy artist', 'active', NULL, ?, ?, ?)
        """,
        [profile_id, owner_user_id, now, now],
    )
    conn.execute(
        """
        INSERT INTO app_artist_membership
            (id, artist_profile_id, user_id, role, status, created_at, updated_at, revoked_at)
        VALUES (?, ?, ?, 'owner', 'active', ?, ?, NULL)
        """,
        [profile_id, profile_id, owner_user_id, now, now],
    )


def test_migration_is_idempotent_and_preserves_metadata(db):
    _legacy_profile(db, profile_id=41, owner_user_id=CLAIMER)
    db.execute("UPDATE app_artist_profile SET bio = 'Legacy bio' WHERE id = 41")

    first = migrate_zero_backed_profile(db, 41)
    second = migrate_zero_backed_profile(db, 41)
    assert first == second
    assert first != INDEPENDENT_ORG_ID

    row = db.execute(
        "SELECT organization_id, bio FROM app_artist_profile WHERE id = 41"
    ).fetchone()
    assert int(row[0]) == first
    assert row[1] == "Legacy bio"
    assert (
        int(
            db.execute(
                "SELECT COUNT(*) FROM app_organization WHERE organization_type = ?",
                [ARTIST_WORKSPACE_TYPE],
            ).fetchone()[0]
        )
        == 1
    )


def test_list_mine_migrates_on_touch(db):
    _legacy_profile(db, profile_id=42, owner_user_id=CLAIMER)
    items = ArtistSpaceUseCases(db).list_mine(CLAIMER)
    assert len(items) == 1
    assert items[0]["organization_id"] != INDEPENDENT_ORG_ID
    summary = ArtistSpaceUseCases(db).summary(artist_profile_id=42, user_id=CLAIMER)
    assert summary["organization_id"] == items[0]["organization_id"]


# ── discovery ──────────────────────────────────────────────────────────────


def test_discover_reports_state_and_single_allowed_action(db):
    uc = ArtistAccessRequestUseCases(db)

    unmanaged = uc.discover(user_id=CLAIMER, search="Free Artist")
    assert unmanaged["total"] == 1
    item = unmanaged["items"][0]
    assert item["management_state"] == "unmanaged"
    assert item["allowed_action"] == "claim_ownership"
    assert item["artist_profile_id"] is None

    request_id = _claim(db)["id"]
    pending = uc.discover(user_id=CLAIMER, search="Free Artist")["items"][0]
    assert pending["management_state"] == "pending"
    assert pending["allowed_action"] == "view_request"
    assert pending["request_id"] == request_id
    assert pending["request_status"] == "pending"

    _approve(db, request_id)
    owned = uc.discover(user_id=CLAIMER, search="Free Artist")["items"][0]
    assert owned["management_state"] == "member"
    assert owned["allowed_action"] == "open_space"
    assert owned["artist_profile_id"] is not None

    outsider = uc.discover(user_id=OTHER, search="Free Artist")["items"][0]
    assert outsider["management_state"] == "managed"
    assert outsider["allowed_action"] == "request_access"


def test_discover_limit_and_empty_search(db):
    uc = ArtistAccessRequestUseCases(db)
    assert uc.discover(user_id=CLAIMER, limit=1)["total"] == 1
    assert uc.discover(user_id=CLAIMER, search="nothing matches")["total"] == 0


# ── profile surface ────────────────────────────────────────────────────────


def test_patch_profile_persists_new_fields_and_identifiers(db):
    profile_id = _approve(db, _claim(db)["id"])["profile"]["id"]
    updated = ArtistSpaceUseCases(db).patch_profile(
        artist_profile_id=profile_id,
        user_id=CLAIMER,
        bio="Independent artist from Quito",
        country_code="ec",
        primary_genre="latin",
        website_url="https://artist.example",
        image_url="https://cdn.example/a.jpg",
        legal_name="Private Legal Name",
        external_identifiers=[{"system_code": "YouTube", "external_value": "chan-1"}],
    )
    assert updated["bio"] == "Independent artist from Quito"
    assert updated["country_code"] == "EC"
    assert updated["primary_genre"] == "latin"
    assert updated["website_url"] == "https://artist.example"
    assert updated["image_url"] == "https://cdn.example/a.jpg"
    assert updated["external_identifiers"] == [
        {"id": 1, "system_code": "youtube", "external_value": "chan-1"}
    ]

    # A second patch must not wipe previously stored additive columns.
    again = ArtistSpaceUseCases(db).patch_profile(
        artist_profile_id=profile_id, user_id=CLAIMER, display_name="Renamed Artist"
    )
    assert again["display_name"] == "Renamed Artist"
    assert again["bio"] == "Independent artist from Quito"
    assert again["legal_name"] == "Private Legal Name"


def test_patch_profile_rejects_bad_values(db):
    profile_id = _approve(db, _claim(db)["id"])["profile"]["id"]
    uc = ArtistSpaceUseCases(db)
    with pytest.raises(ValidationError):
        uc.patch_profile(
            artist_profile_id=profile_id, user_id=CLAIMER, country_code="Ecuador"
        )
    with pytest.raises(ValidationError):
        uc.patch_profile(
            artist_profile_id=profile_id, user_id=CLAIMER, website_url="not-a-url"
        )
    with pytest.raises(ConflictError):
        uc.patch_profile(
            artist_profile_id=profile_id,
            user_id=CLAIMER,
            external_identifiers=[
                {"system_code": "spotify", "external_value": "a"},
                {"system_code": "spotify", "external_value": "b"},
            ],
        )


def test_new_capabilities_are_role_scoped(db):
    assert "artist_space.release.submit" in permissions_for_role("owner")
    assert "artist_space.release.submit" in permissions_for_role("administrator")
    assert "artist_space.release.submit" not in permissions_for_role("member")
    assert "artist_space.release.create" in permissions_for_role("member")
    assert permissions_for_role("reader") == [
        "artist_space.catalog.view",
        "artist_space.view",
    ]
