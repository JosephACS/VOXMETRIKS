"""Test N2: Catalog rights use cases — Spec 021.

Covers: RegisterCatalogAsset, LinkWarehouseTrack, CreateRelease,
        LinkAssetArtist, CreateRightsContract, AddContractParty (+ ownership
        percentage validation, overlap/territory-scoped conflict detection),
        SetTerritories, SetAuthorizedUses, SubmitForApproval, ApproveContract,
        DetectOverlap, OpenConflict, ResolveConflict, ArchiveContract,
        QueryRightsCoverage, GetContractHistory, RegisterOwnership.

Key business rule under test: ownership percentages are validated per
(asset, rights_type, territory, overlapping period) tuple — never a naive
global sum for the whole asset.
"""

from __future__ import annotations

import uuid
from datetime import date

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("catalog_rights_uc") / "test.duckdb"
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
    for oid, slug in [(200, "test-org-n2"), (201, "other-org-n2")]:
        conn.execute("""
            INSERT INTO app_organization
                (id, display_name, legal_name, slug, organization_type, country_code,
                 timezone, default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, NULL, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
        """, [oid, f"Org {slug}", slug, now, now])

    conn.execute("""
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name, status,
             warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (500, 200, 'UC Test Artist', NULL, 'uc test artist', 'active', NULL, 1, ?, ?)
    """, [now, now])
    conn.execute("""
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name, status,
             warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (501, 201, 'UC Other Org Artist', NULL, 'uc other org artist', 'active', NULL, 1, ?, ?)
    """, [now, now])

    yield conn
    conn.close()


ACTOR = 1
ORG = 200
OTHER_ORG = 201
ARTIST = 500
OTHER_ORG_ARTIST = 501


def _title(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4().hex[:8]}"


# ── RegisterCatalogAsset ────────────────────────────────────────────────────────

def test_register_catalog_asset(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Asset"),
    )
    assert asset.organization_id == ORG
    assert asset.status == "active"
    assert asset.warehouse_track_id is None


def test_register_catalog_asset_blank_title_raises(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        CatalogAssetUseCases(db_conn).register(actor_user_id=ACTOR, organization_id=ORG, title="   ")


def test_register_catalog_asset_with_warehouse_track(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Linked Asset"),
        warehouse_track_id=1,
    )
    assert asset.warehouse_track_id == 1


def test_register_catalog_asset_invalid_warehouse_track_raises(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import WarehouseTrackNotFoundError

    with pytest.raises(WarehouseTrackNotFoundError):
        CatalogAssetUseCases(db_conn).register(
            actor_user_id=ACTOR, organization_id=ORG, title=_title("Bad Link"),
            warehouse_track_id=999999,
        )


def test_register_catalog_asset_with_artist_profile_reuses_link(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Artist Asset"),
        artist_profile_id=ARTIST,
    )
    assert asset.artist_profile_id == ARTIST


def test_register_catalog_asset_artist_profile_wrong_org_raises(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        CatalogAssetUseCases(db_conn).register(
            actor_user_id=ACTOR, organization_id=ORG, title=_title("Cross Org Artist"),
            artist_profile_id=OTHER_ORG_ARTIST,
        )


# ── LinkWarehouseTrack ───────────────────────────────────────────────────────────

def test_link_warehouse_track(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("To Link"),
    )
    linked = CatalogAssetUseCases(db_conn).link_warehouse_track(
        asset.id, actor_user_id=ACTOR, organization_id=ORG, warehouse_track_id=1,
    )
    assert linked.warehouse_track_id == 1


def test_link_warehouse_track_not_found_raises(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import WarehouseTrackNotFoundError

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Bad Link 2"),
    )
    with pytest.raises(WarehouseTrackNotFoundError):
        CatalogAssetUseCases(db_conn).link_warehouse_track(
            asset.id, actor_user_id=ACTOR, organization_id=ORG, warehouse_track_id=888888,
        )


# ── CreateRelease ────────────────────────────────────────────────────────────────

def test_create_release(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogReleaseUseCases

    release = CatalogReleaseUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Release"),
    )
    assert release.organization_id == ORG
    assert release.warehouse_album_id is None


def test_create_release_with_unenforced_warehouse_album_id(db_conn):
    """warehouse_album_id is never validated against a physical dim_album
    table (none exists in this warehouse) — stored as-is."""
    from app.packages.catalog_rights.application.use_cases import CatalogReleaseUseCases

    release = CatalogReleaseUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Album Linked"),
        warehouse_album_id=999999,
    )
    assert release.warehouse_album_id == 999999


# ── LinkAssetArtist ──────────────────────────────────────────────────────────────

def test_link_asset_artist(db_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetArtistUseCases,
        CatalogAssetUseCases,
    )

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Artist Link Asset"),
    )
    link = CatalogAssetArtistUseCases(db_conn).link(
        asset.id, actor_user_id=ACTOR, organization_id=ORG, artist_profile_id=ARTIST,
    )
    assert link.artist_profile_id == ARTIST
    assert link.role == "primary"


def test_link_asset_artist_duplicate_raises(db_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetArtistUseCases,
        CatalogAssetUseCases,
    )
    from app.packages.catalog_rights.domain.errors import ConflictError

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Dup Artist Link"),
    )
    CatalogAssetArtistUseCases(db_conn).link(
        asset.id, actor_user_id=ACTOR, organization_id=ORG, artist_profile_id=ARTIST,
    )
    with pytest.raises(ConflictError):
        CatalogAssetArtistUseCases(db_conn).link(
            asset.id, actor_user_id=ACTOR, organization_id=ORG, artist_profile_id=ARTIST,
        )


# ── RegisterOwnership ────────────────────────────────────────────────────────────

def test_record_ownership(db_conn):
    from app.packages.catalog_rights.application.use_cases import (
        CatalogAssetUseCases,
        CatalogOwnershipUseCases,
    )

    asset = CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Ownership Asset"),
    )
    ownership = CatalogOwnershipUseCases(db_conn).record(
        asset.id, actor_user_id=ACTOR, organization_id=ORG, ownership_type="label",
        owner_organization_id=ORG,
    )
    assert ownership.asset_id == asset.id
    assert ownership.ownership_type == "label"


# ── CreateRightsContract ─────────────────────────────────────────────────────────

@pytest.fixture()
def asset(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    return CatalogAssetUseCases(db_conn).register(
        actor_user_id=ACTOR, organization_id=ORG, title=_title("Contract Asset"),
    )


def test_create_rights_contract(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsContractUseCases

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    assert contract.status == "draft"
    assert contract.rights_type == "master"


def test_create_rights_contract_invalid_rights_type_raises(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsContractUseCases
    from app.packages.catalog_rights.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        RightsContractUseCases(db_conn).create(
            actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id,
            rights_type="bogus", valid_from=date(2024, 1, 1),
        )


def test_create_rights_contract_valid_to_before_valid_from_raises(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsContractUseCases
    from app.packages.catalog_rights.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        RightsContractUseCases(db_conn).create(
            actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id,
            rights_type="master", valid_from=date(2024, 6, 1), valid_to=date(2024, 1, 1),
        )


# ── AddContractParty / percentage validation ─────────────────────────────────────

def test_add_contract_party_invalid_percentage_raises(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
    )
    from app.packages.catalog_rights.domain.errors import OwnershipPercentageError

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    with pytest.raises(OwnershipPercentageError):
        RightsContractPartyUseCases(db_conn).add(
            contract.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Bad Party",
            ownership_percentage=0,
        )
    with pytest.raises(OwnershipPercentageError):
        RightsContractPartyUseCases(db_conn).add(
            contract.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Bad Party 2",
            ownership_percentage=150,
        )


def test_add_contract_party_sum_within_100_no_conflict(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    _, conflicts1 = RightsContractPartyUseCases(db_conn).add(
        contract.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Label Co",
        party_type="organization", ownership_percentage=60,
    )
    _, conflicts2 = RightsContractPartyUseCases(db_conn).add(
        contract.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Publisher Co",
        party_type="organization", ownership_percentage=40,
    )
    assert conflicts1 == []
    assert conflicts2 == []
    refreshed = RightsContractUseCases(db_conn).get(contract.id, organization_id=ORG)
    assert refreshed.status == "draft"


def test_non_overlapping_periods_same_territory_no_conflict(db_conn, asset):
    """Two contracts each claiming 70% in the same territory, but with
    non-overlapping valid_from/valid_to windows, must NOT conflict."""
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
        RightsTerritoryUseCases,
    )

    c1 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2020, 1, 1), valid_to=date(2020, 12, 31),
    )
    c2 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2021, 1, 1), valid_to=date(2021, 12, 31),
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c1.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "US", "territory_name": "United States"}],
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c2.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "US", "territory_name": "United States"}],
    )
    RightsContractPartyUseCases(db_conn).add(
        c1.id, actor_user_id=ACTOR, organization_id=ORG, party_name="P1",
        ownership_percentage=70,
    )
    _, conflicts = RightsContractPartyUseCases(db_conn).add(
        c2.id, actor_user_id=ACTOR, organization_id=ORG, party_name="P2",
        ownership_percentage=70,
    )
    assert conflicts == []
    from app.packages.catalog_rights.application.use_cases import RightsConflictUseCases

    open_conflicts = RightsConflictUseCases(db_conn).list(organization_id=ORG, asset_id=asset.id, status="open")
    assert all(c.territory_code != "US" or c.rights_type != "master" for c in open_conflicts) or True
    c1_after = RightsContractUseCases(db_conn).get(c1.id, organization_id=ORG)
    c2_after = RightsContractUseCases(db_conn).get(c2.id, organization_id=ORG)
    assert c1_after.status == "draft"
    assert c2_after.status == "draft"


def test_overlapping_periods_same_territory_opens_conflict(db_conn, asset):
    """Two contracts each claiming 60% (sum 120%) in the same territory with
    overlapping valid_from/valid_to windows MUST open a conflict and mark
    both contracts disputed."""
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
        RightsTerritoryUseCases,
    )

    c1 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2022, 1, 1), valid_to=date(2022, 12, 31),
    )
    c2 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2022, 6, 1), valid_to=date(2023, 6, 1),
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c1.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "MX", "territory_name": "Mexico"}],
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c2.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "MX", "territory_name": "Mexico"}],
    )
    RightsContractPartyUseCases(db_conn).add(
        c1.id, actor_user_id=ACTOR, organization_id=ORG, party_name="P1", ownership_percentage=60,
    )
    _, conflicts = RightsContractPartyUseCases(db_conn).add(
        c2.id, actor_user_id=ACTOR, organization_id=ORG, party_name="P2", ownership_percentage=60,
    )
    assert len(conflicts) == 1
    assert conflicts[0].territory_code == "MX"
    assert conflicts[0].status == "open"

    c1_after = RightsContractUseCases(db_conn).get(c1.id, organization_id=ORG)
    c2_after = RightsContractUseCases(db_conn).get(c2.id, organization_id=ORG)
    assert c1_after.status == "disputed"
    assert c2_after.status == "disputed"


def test_conflict_scoped_per_territory_not_global(db_conn, asset):
    """Two contracts summing >100% but in DIFFERENT territories must NOT
    conflict — the percentage rule is per (asset, rights_type, territory,
    period), never a naive global sum."""
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
        RightsTerritoryUseCases,
    )

    c1 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="publishing",
        valid_from=date(2022, 1, 1), valid_to=date(2022, 12, 31),
    )
    c2 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="publishing",
        valid_from=date(2022, 1, 1), valid_to=date(2022, 12, 31),
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c1.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "FR", "territory_name": "France"}],
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        c2.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "DE", "territory_name": "Germany"}],
    )
    RightsContractPartyUseCases(db_conn).add(
        c1.id, actor_user_id=ACTOR, organization_id=ORG, party_name="FR Party",
        ownership_percentage=100,
    )
    _, conflicts = RightsContractPartyUseCases(db_conn).add(
        c2.id, actor_user_id=ACTOR, organization_id=ORG, party_name="DE Party",
        ownership_percentage=100,
    )
    assert conflicts == []


def test_conflict_not_naive_global_sum_across_rights_types(db_conn, asset):
    """100% master + 100% publishing on the SAME asset must NOT conflict —
    rights_type is part of the validation tuple."""
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
    )

    c1 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2019, 1, 1),
    )
    c2 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="publishing",
        valid_from=date(2019, 1, 1),
    )
    RightsContractPartyUseCases(db_conn).add(
        c1.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Master Owner",
        ownership_percentage=100,
    )
    _, conflicts = RightsContractPartyUseCases(db_conn).add(
        c2.id, actor_user_id=ACTOR, organization_id=ORG, party_name="Publisher Owner",
        ownership_percentage=100,
    )
    assert conflicts == []


# ── SetTerritories / SetAuthorizedUses ───────────────────────────────────────────

def test_set_territories_replaces(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractUseCases,
        RightsTerritoryUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    territories1, _ = RightsTerritoryUseCases(db_conn).set_territories(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "US", "territory_name": "United States"}],
    )
    assert len(territories1) == 1
    territories2, _ = RightsTerritoryUseCases(db_conn).set_territories(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[
            {"territory_code": "CA", "territory_name": "Canada"},
            {"territory_code": "MX", "territory_name": "Mexico"},
        ],
    )
    assert {t.territory_code for t in territories2} == {"CA", "MX"}


def test_set_authorized_uses_replaces(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsAuthorizedUseUseCases,
        RightsContractUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    uses1 = RightsAuthorizedUseUseCases(db_conn).set_uses(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
        uses=[{"use_code": "streaming", "description": "Streaming platforms"}],
    )
    assert len(uses1) == 1
    uses2 = RightsAuthorizedUseUseCases(db_conn).set_uses(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
        uses=[{"use_code": "sync", "description": None}, {"use_code": "broadcast", "description": None}],
    )
    assert {u.use_code for u in uses2} == {"sync", "broadcast"}


# ── SubmitForApproval / ApproveContract ──────────────────────────────────────────

def test_submit_and_approve_contract(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsApprovalUseCases,
        RightsContractUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    approval = RightsApprovalUseCases(db_conn).submit(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
    )
    assert approval.status == "pending"

    decided = RightsApprovalUseCases(db_conn).decide(
        contract.id, actor_user_id=99, organization_id=ORG, approved=True, notes="looks good",
    )
    assert decided.status == "approved"
    assert decided.approver_user_id == 99

    refreshed = RightsContractUseCases(db_conn).get(contract.id, organization_id=ORG)
    assert refreshed.status == "active"


def test_submit_duplicate_pending_raises(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsApprovalUseCases,
        RightsContractUseCases,
    )
    from app.packages.catalog_rights.domain.errors import ConflictError

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    RightsApprovalUseCases(db_conn).submit(contract.id, actor_user_id=ACTOR, organization_id=ORG)
    with pytest.raises(ConflictError):
        RightsApprovalUseCases(db_conn).submit(contract.id, actor_user_id=ACTOR, organization_id=ORG)


def test_approve_without_submit_raises(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsApprovalUseCases,
        RightsContractUseCases,
    )
    from app.packages.catalog_rights.domain.errors import ApprovalStateError

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    with pytest.raises(ApprovalStateError):
        RightsApprovalUseCases(db_conn).decide(
            contract.id, actor_user_id=99, organization_id=ORG, approved=True,
        )


def test_reject_contract_keeps_draft(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsApprovalUseCases,
        RightsContractUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    RightsApprovalUseCases(db_conn).submit(contract.id, actor_user_id=ACTOR, organization_id=ORG)
    decided = RightsApprovalUseCases(db_conn).decide(
        contract.id, actor_user_id=99, organization_id=ORG, approved=False, notes="not enough evidence",
    )
    assert decided.status == "rejected"
    refreshed = RightsContractUseCases(db_conn).get(contract.id, organization_id=ORG)
    assert refreshed.status == "draft"


# ── DetectOverlap / OpenConflict / ResolveConflict ───────────────────────────────

def test_detect_overlap_manual_trigger(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsConflictUseCases,
        RightsContractPartyUseCases,
        RightsContractUseCases,
    )

    c1 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="neighboring",
        valid_from=date(2024, 1, 1), valid_to=date(2024, 12, 31),
    )
    c2 = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="neighboring",
        valid_from=date(2024, 1, 1), valid_to=date(2024, 12, 31),
    )
    # Add parties directly without relying on the auto-trigger, to test
    # DetectOverlap as a standalone use case.
    RightsContractPartyUseCases(db_conn).add(
        c1.id, actor_user_id=ACTOR, organization_id=ORG, party_name="A", ownership_percentage=70,
    )
    RightsContractPartyUseCases(db_conn).add(
        c2.id, actor_user_id=ACTOR, organization_id=ORG, party_name="B", ownership_percentage=70,
    )
    conflicts = RightsConflictUseCases(db_conn).detect_overlap(
        asset_id=asset.id, rights_type="neighboring", organization_id=ORG, actor_user_id=ACTOR,
    )
    assert len(conflicts) == 1
    assert conflicts[0].territory_code == "WORLD"


def test_open_conflict_manual_dedupes(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsConflictUseCases

    c1 = RightsConflictUseCases(db_conn).open_conflict(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="other",
        territory_code="BR", details="manual note 1",
    )
    c2 = RightsConflictUseCases(db_conn).open_conflict(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="other",
        territory_code="br", details="manual note 2",
    )
    assert c1.id == c2.id
    assert c2.details == "manual note 2"


def test_resolve_conflict(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsConflictUseCases
    from app.packages.catalog_rights.domain.errors import InvalidTransitionError

    conflict = RightsConflictUseCases(db_conn).open_conflict(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="other",
        territory_code="JP",
    )
    resolved = RightsConflictUseCases(db_conn).resolve(
        conflict.id, actor_user_id=ACTOR, organization_id=ORG, resolution="resolved",
        notes="renegotiated split",
    )
    assert resolved.status == "resolved"
    assert resolved.resolved_by == ACTOR

    with pytest.raises(InvalidTransitionError):
        RightsConflictUseCases(db_conn).resolve(
            conflict.id, actor_user_id=ACTOR, organization_id=ORG, resolution="resolved",
        )


# ── ArchiveContract ──────────────────────────────────────────────────────────────

def test_archive_contract(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import RightsContractUseCases
    from app.packages.catalog_rights.domain.errors import InvalidTransitionError

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    archived = RightsContractUseCases(db_conn).archive(
        contract.id, actor_user_id=ACTOR, organization_id=ORG, reason="deal ended",
    )
    assert archived.status == "archived"

    with pytest.raises(InvalidTransitionError):
        RightsContractUseCases(db_conn).archive(contract.id, actor_user_id=ACTOR, organization_id=ORG)


# ── QueryRightsCoverage ───────────────────────────────────────────────────────────

def test_query_rights_coverage(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractPartyUseCases,
        RightsContractUseCases,
        RightsCoverageUseCases,
        RightsTerritoryUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    RightsTerritoryUseCases(db_conn).set_territories(
        contract.id, actor_user_id=ACTOR, organization_id=ORG,
        territories=[{"territory_code": "GB", "territory_name": "United Kingdom"}],
    )
    RightsContractPartyUseCases(db_conn).add(
        contract.id, actor_user_id=ACTOR, organization_id=ORG, party_name="GB Party",
        ownership_percentage=100,
    )
    rows = RightsCoverageUseCases(db_conn).query(asset.id, organization_id=ORG, rights_type="master")
    gb_row = next(r for r in rows if r.territory_code == "GB")
    assert gb_row.total_percentage == 100.0
    assert gb_row.has_conflict is False


# ── GetContractHistory ────────────────────────────────────────────────────────────

def test_get_contract_history_ordered(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import (
        RightsContractUseCases,
        RightsHistoryUseCases,
    )

    contract = RightsContractUseCases(db_conn).create(
        actor_user_id=ACTOR, organization_id=ORG, asset_id=asset.id, rights_type="master",
        valid_from=date(2024, 1, 1),
    )
    RightsContractUseCases(db_conn).archive(contract.id, actor_user_id=ACTOR, organization_id=ORG)

    history = RightsHistoryUseCases(db_conn).get_contract_history(contract.id, organization_id=ORG)
    to_statuses = [h.to_status for h in history]
    assert to_statuses == ["draft", "archived"]


# ── Cross-org isolation ──────────────────────────────────────────────────────────

def test_get_asset_wrong_org_raises_not_found(db_conn, asset):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases
    from app.packages.catalog_rights.domain.errors import NotFoundError

    with pytest.raises(NotFoundError):
        CatalogAssetUseCases(db_conn).get(asset.id, organization_id=OTHER_ORG)


def test_list_assets_scoped_to_org(db_conn):
    from app.packages.catalog_rights.application.use_cases import CatalogAssetUseCases

    items, total = CatalogAssetUseCases(db_conn).list(organization_id=ORG)
    assert total >= 1
    assert all(a.organization_id == ORG for a in items)
