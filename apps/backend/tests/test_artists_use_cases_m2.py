"""Test M2: Artists use cases — Spec 020.

Covers: CreateArtistProfile (+ duplicate rejection), ActivateArtist,
        DeactivateArtist, ArchiveArtist (+ invalid transitions),
        LinkOrganization, AssignManager (+ duplicate rejection),
        AddTeamMember, RemoveTeamMember, SetExternalIdentifier (upsert),
        LinkWarehouseArtist (+ not found), TransferArtistOrganization (audited),
        GetHistory ordering.
"""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("artists_uc") / "test.duckdb"
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

    # Restore the global schema-ready flag immediately: it must only be
    # False for the duration of this fixture's own ensure_* calls against
    # its private tmp-path connection, not for the whole test module (other
    # test files sharing the process must see the real value).
    schema_bootstrap._schema_ready = previous

    now = utc_now()
    for oid, slug in [(100, "test-org-m2"), (101, "other-org-m2")]:
        conn.execute("""
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, NULL, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
        """, [oid, f"Org {slug}", slug, now, now])

    yield conn
    conn.close()


ACTOR = 1
ORG = 100
OTHER_ORG = 101


# ── CreateArtistProfile ────────────────────────────────────────────────────────

def test_create_artist_profile(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, display_name="  The Voxmetriks  ",
        legal_name="Voxmetriks LLC",
    )
    assert artist.organization_id == ORG
    assert artist.display_name == "The Voxmetriks"
    assert artist.normalized_name == "the voxmetriks"
    assert artist.status == "draft"


def test_create_artist_profile_duplicate_raises(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import DuplicateArtistError

    with pytest.raises(DuplicateArtistError):
        ArtistProfileUseCases(db_conn).create(
            actor_user_id=ACTOR, organization_id=ORG, display_name="the voxmetriks",
        )


def test_create_artist_profile_same_name_different_org_allowed(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=OTHER_ORG, display_name="The Voxmetriks",
    )
    assert artist.organization_id == OTHER_ORG


def test_create_artist_profile_blank_name_raises(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        ArtistProfileUseCases(db_conn).create(
            actor_user_id=ACTOR, organization_id=ORG, display_name="   ",
        )


def test_create_artist_profile_creates_primary_org_link(db_conn):
    from app.packages.artists.application.use_cases import (
        ArtistOrganizationUseCases,
        ArtistProfileUseCases,
    )

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, display_name="Primary Link Artist",
    )
    links = ArtistOrganizationUseCases(db_conn).list_for_artist(artist.id)
    assert len(links) == 1
    assert links[0].is_primary is True
    assert links[0].relationship_role == "primary"
    assert links[0].organization_id == ORG


# ── Status transitions ─────────────────────────────────────────────────────────

@pytest.fixture()
def draft_artist(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    import uuid

    return ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG,
        display_name=f"Transition Artist {uuid.uuid4().hex[:8]}",
    )


def test_activate_artist(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    activated = ArtistProfileUseCases(db_conn).activate(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert activated.status == "active"


def test_deactivate_artist(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    ArtistProfileUseCases(db_conn).activate(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)
    deactivated = ArtistProfileUseCases(db_conn).deactivate(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, reason="on hiatus",
    )
    assert deactivated.status == "inactive"


def test_reactivate_from_inactive(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    ArtistProfileUseCases(db_conn).activate(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)
    ArtistProfileUseCases(db_conn).deactivate(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)
    reactivated = ArtistProfileUseCases(db_conn).activate(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert reactivated.status == "active"


def test_archive_artist_is_terminal(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import InvalidTransitionError

    archived = ArtistProfileUseCases(db_conn).archive(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, reason="retired",
    )
    assert archived.status == "archived"

    with pytest.raises(InvalidTransitionError):
        ArtistProfileUseCases(db_conn).activate(
            draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        )


def test_get_history_ordered(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import (
        ArtistHistoryUseCases,
        ArtistProfileUseCases,
    )

    ArtistProfileUseCases(db_conn).activate(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)
    ArtistProfileUseCases(db_conn).deactivate(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)
    ArtistProfileUseCases(db_conn).archive(draft_artist.id, actor_user_id=ACTOR, organization_id=ORG)

    history = ArtistHistoryUseCases(db_conn).get_history(draft_artist.id, organization_id=ORG)
    to_statuses = [h.to_status for h in history]
    assert to_statuses == ["draft", "active", "inactive", "archived"]


# ── LinkOrganization ────────────────────────────────────────────────────────────

def test_link_organization_secondary(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistOrganizationUseCases

    link = ArtistOrganizationUseCases(db_conn).link(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        target_organization_id=OTHER_ORG, relationship_role="licensed",
    )
    assert link.organization_id == OTHER_ORG
    assert link.is_primary is False
    assert link.relationship_role == "licensed"


def test_link_organization_duplicate_raises(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistOrganizationUseCases
    from app.packages.artists.domain.errors import ConflictError

    ArtistOrganizationUseCases(db_conn).link(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        target_organization_id=OTHER_ORG,
    )
    with pytest.raises(ConflictError):
        ArtistOrganizationUseCases(db_conn).link(
            draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
            target_organization_id=OTHER_ORG,
        )


# ── AssignManager ────────────────────────────────────────────────────────────────

def test_assign_manager(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistAssignmentUseCases

    assignment = ArtistAssignmentUseCases(db_conn).assign_manager(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, user_id=2,
    )
    assert assignment.status == "active"
    assert assignment.role == "manager"


def test_assign_manager_duplicate_raises(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistAssignmentUseCases
    from app.packages.artists.domain.errors import ConflictError

    ArtistAssignmentUseCases(db_conn).assign_manager(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, user_id=3,
    )
    with pytest.raises(ConflictError):
        ArtistAssignmentUseCases(db_conn).assign_manager(
            draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, user_id=3,
        )


def test_end_assignment(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistAssignmentUseCases

    assignment = ArtistAssignmentUseCases(db_conn).assign_manager(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, user_id=4,
    )
    ended = ArtistAssignmentUseCases(db_conn).end_assignment(
        assignment.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert ended.status == "ended"
    assert ended.ended_at is not None

    # Re-assigning the same user after ending is allowed
    reassigned = ArtistAssignmentUseCases(db_conn).assign_manager(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG, user_id=4,
    )
    assert reassigned.status == "active"


# ── Team membership ────────────────────────────────────────────────────────────

def test_add_and_remove_team_member(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistTeamUseCases
    from app.packages.artists.domain.errors import ConflictError

    member = ArtistTeamUseCases(db_conn).add_member(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        user_id=5, team_role="tour_manager",
    )
    assert member.status == "active"
    assert member.team_role == "tour_manager"

    with pytest.raises(ConflictError):
        ArtistTeamUseCases(db_conn).add_member(
            draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
            user_id=5, team_role="producer",
        )

    removed = ArtistTeamUseCases(db_conn).remove_member(
        member.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert removed.status == "removed"
    assert removed.removed_at is not None


def test_list_team_for_artist(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistTeamUseCases

    ArtistTeamUseCases(db_conn).add_member(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        user_id=6, team_role="producer",
    )
    members = ArtistTeamUseCases(db_conn).list_for_artist(draft_artist.id)
    assert any(m.user_id == 6 for m in members)


# ── External identifiers ────────────────────────────────────────────────────────

def test_set_external_identifier_creates_then_updates(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistExternalIdentifierUseCases

    created = ArtistExternalIdentifierUseCases(db_conn).set_identifier(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        system_code="spotify", external_value="spotify-artist-id-1",
    )
    assert created.external_value == "spotify-artist-id-1"

    updated = ArtistExternalIdentifierUseCases(db_conn).set_identifier(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        system_code="spotify", external_value="spotify-artist-id-2",
    )
    assert updated.id == created.id
    assert updated.external_value == "spotify-artist-id-2"

    identifiers = ArtistExternalIdentifierUseCases(db_conn).list_for_artist(draft_artist.id)
    spotify_entries = [i for i in identifiers if i.system_code == "spotify"]
    assert len(spotify_entries) == 1


# ── LinkWarehouseArtist ─────────────────────────────────────────────────────────

def test_link_warehouse_artist(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    linked = ArtistProfileUseCases(db_conn).link_warehouse_artist(
        draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
        warehouse_artist_id=1,
    )
    assert linked.warehouse_artist_id == 1


def test_link_warehouse_artist_not_found_raises(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import WarehouseArtistNotFoundError

    with pytest.raises(WarehouseArtistNotFoundError):
        ArtistProfileUseCases(db_conn).link_warehouse_artist(
            draft_artist.id, actor_user_id=ACTOR, organization_id=ORG,
            warehouse_artist_id=999999,
        )


def test_create_with_warehouse_artist_id(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    import uuid

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG,
        display_name=f"Linked At Creation {uuid.uuid4().hex[:8]}",
        warehouse_artist_id=1,
    )
    assert artist.warehouse_artist_id == 1


# ── TransferArtistOrganization ──────────────────────────────────────────────────

def test_transfer_artist_organization(db_conn):
    from app.packages.artists.application.use_cases import (
        ArtistOrganizationUseCases,
        ArtistProfileUseCases,
    )
    import uuid

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG,
        display_name=f"Transfer Artist {uuid.uuid4().hex[:8]}",
    )
    transferred = ArtistProfileUseCases(db_conn).transfer_organization(
        artist.id, actor_user_id=ACTOR, organization_id=ORG,
        target_organization_id=OTHER_ORG, reason="ownership change",
    )
    assert transferred.organization_id == OTHER_ORG

    links = ArtistOrganizationUseCases(db_conn).list_for_artist(artist.id)
    primary_links = [l for l in links if l.is_primary]
    active_primary = [l for l in primary_links if l.status == "active"]
    assert len(active_primary) == 1
    assert active_primary[0].organization_id == OTHER_ORG

    audit_row = db_conn.execute(
        "SELECT action FROM app_audit_log WHERE target_type = 'artist_profile' "
        "AND target_id = ? AND action = 'artist_profile.transferred'",
        [str(artist.id)],
    ).fetchone()
    assert audit_row is not None


def test_transfer_artist_organization_same_org_raises(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import ValidationError
    import uuid

    artist = ArtistProfileUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG,
        display_name=f"Same Org Transfer {uuid.uuid4().hex[:8]}",
    )
    with pytest.raises(ValidationError):
        ArtistProfileUseCases(db_conn).transfer_organization(
            artist.id, actor_user_id=ACTOR, organization_id=ORG,
            target_organization_id=ORG,
        )


# ── Cross-org isolation ─────────────────────────────────────────────────────────

def test_get_artist_wrong_org_raises_not_found(db_conn, draft_artist):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases
    from app.packages.artists.domain.errors import NotFoundError

    with pytest.raises(NotFoundError):
        ArtistProfileUseCases(db_conn).get(draft_artist.id, organization_id=OTHER_ORG)


# ── ListArtists ──────────────────────────────────────────────────────────────────

def test_list_artists_scoped_to_org(db_conn):
    from app.packages.artists.application.use_cases import ArtistProfileUseCases

    items, total = ArtistProfileUseCases(db_conn).list(organization_id=ORG)
    assert total >= 1
    assert all(a.organization_id == ORG for a in items)
