"""Catalog rights HTTP router — Spec 021.

All endpoints under /catalog-rights prefix. Mounted at
/api/v1/catalog-rights in main.py.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.catalog_rights.application.use_cases import (
    CatalogAssetArtistUseCases,
    CatalogAssetUseCases,
    CatalogOwnershipUseCases,
    CatalogReleaseUseCases,
    RightsApprovalUseCases,
    RightsAuthorizedUseUseCases,
    RightsConflictUseCases,
    RightsContractPartyUseCases,
    RightsContractUseCases,
    RightsCoverageUseCases,
    RightsHistoryUseCases,
    RightsTerritoryUseCases,
)
from app.packages.catalog_rights.domain.errors import CatalogRightsError
from app.packages.catalog_rights.presentation.dependencies import require_org_rights_permission
from app.packages.catalog_rights.presentation.error_mapping import raise_catalog_rights_http
from app.packages.catalog_rights.presentation.schemas import (
    AddContractPartyRequest,
    AddContractPartyResponse,
    ApproveContractRequest,
    AuthorizedUseInput,
    CatalogAssetArtistOut,
    CatalogAssetCreateRequest,
    CatalogAssetOut,
    CatalogOwnershipOut,
    CatalogReleaseCreateRequest,
    CatalogReleaseOut,
    ContractTransitionRequest,
    DetectOverlapRequest,
    LinkAssetArtistRequest,
    LinkWarehouseTrackRequest,
    OpenConflictRequest,
    PaginatedAssets,
    PaginatedContracts,
    PaginatedReleases,
    RegisterOwnershipRequest,
    ResolveConflictRequest,
    RightsApprovalOut,
    RightsAuthorizedUseOut,
    RightsConflictOut,
    RightsContractCreateRequest,
    RightsContractOut,
    RightsContractPartyOut,
    RightsCoverageRowOut,
    RightsStatusHistoryOut,
    RightsTerritoryOut,
    SetAuthorizedUsesRequest,
    SetTerritoriesRequest,
    SetTerritoriesResponse,
)

catalog_rights_router = APIRouter(prefix="/catalog-rights", tags=["Catalog Rights"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


# ── CatalogAsset ──────────────────────────────────────────────────────────────

@catalog_rights_router.get("/assets", response_model=PaginatedAssets)
def list_assets(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> PaginatedAssets:
    p, ps, offset = _page(page, page_size)
    items, total = CatalogAssetUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedAssets(
        items=[CatalogAssetOut(**a.__dict__) for a in items], total=total, page=p, page_size=ps,
    )


@catalog_rights_router.post("/assets", response_model=CatalogAssetOut, status_code=201)
def register_asset(
    body: CatalogAssetCreateRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> CatalogAssetOut:
    try:
        asset = CatalogAssetUseCases(ctx["conn"]).register(
            actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            title=body.title, status=body.status, warehouse_track_id=body.warehouse_track_id,
            artist_profile_id=body.artist_profile_id, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogAssetOut(**asset.__dict__)


@catalog_rights_router.get("/assets/{asset_id}", response_model=CatalogAssetOut)
def get_asset(
    asset_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> CatalogAssetOut:
    try:
        asset = CatalogAssetUseCases(ctx["conn"]).get(asset_id, organization_id=ctx["organization_id"])
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogAssetOut(**asset.__dict__)


@catalog_rights_router.post("/assets/{asset_id}/link-warehouse-track", response_model=CatalogAssetOut)
def link_warehouse_track(
    asset_id: int,
    body: LinkWarehouseTrackRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.update")),
) -> CatalogAssetOut:
    try:
        asset = CatalogAssetUseCases(ctx["conn"]).link_warehouse_track(
            asset_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            warehouse_track_id=body.warehouse_track_id, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogAssetOut(**asset.__dict__)


@catalog_rights_router.get("/assets/{asset_id}/artists", response_model=list[CatalogAssetArtistOut])
def list_asset_artists(
    asset_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[CatalogAssetArtistOut]:
    CatalogAssetUseCases(ctx["conn"]).get(asset_id, organization_id=ctx["organization_id"])
    items = CatalogAssetArtistUseCases(ctx["conn"]).list_for_asset(asset_id)
    return [CatalogAssetArtistOut(**i.__dict__) for i in items]


@catalog_rights_router.post(
    "/assets/{asset_id}/artists", response_model=CatalogAssetArtistOut, status_code=201
)
def link_asset_artist(
    asset_id: int,
    body: LinkAssetArtistRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> CatalogAssetArtistOut:
    try:
        link = CatalogAssetArtistUseCases(ctx["conn"]).link(
            asset_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            artist_profile_id=body.artist_profile_id, role=body.role, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogAssetArtistOut(**link.__dict__)


@catalog_rights_router.get("/assets/{asset_id}/ownership", response_model=list[CatalogOwnershipOut])
def list_ownership(
    asset_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[CatalogOwnershipOut]:
    CatalogAssetUseCases(ctx["conn"]).get(asset_id, organization_id=ctx["organization_id"])
    items = CatalogOwnershipUseCases(ctx["conn"]).list_for_asset(asset_id)
    return [CatalogOwnershipOut(**i.__dict__) for i in items]


@catalog_rights_router.post(
    "/assets/{asset_id}/ownership", response_model=CatalogOwnershipOut, status_code=201
)
def register_ownership(
    asset_id: int,
    body: RegisterOwnershipRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> CatalogOwnershipOut:
    try:
        ownership = CatalogOwnershipUseCases(ctx["conn"]).record(
            asset_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            ownership_type=body.ownership_type, owner_organization_id=body.owner_organization_id,
            artist_profile_id=body.artist_profile_id, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogOwnershipOut(**ownership.__dict__)


@catalog_rights_router.get("/assets/{asset_id}/coverage", response_model=list[RightsCoverageRowOut])
def query_rights_coverage(
    asset_id: int,
    rights_type: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsCoverageRowOut]:
    try:
        rows = RightsCoverageUseCases(ctx["conn"]).query(
            asset_id, organization_id=ctx["organization_id"], rights_type=rights_type,
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return [RightsCoverageRowOut(**r.__dict__) for r in rows]


@catalog_rights_router.post("/assets/{asset_id}/detect-overlap", response_model=list[RightsConflictOut])
def detect_overlap(
    asset_id: int,
    body: DetectOverlapRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.conflict")),
) -> list[RightsConflictOut]:
    try:
        CatalogAssetUseCases(ctx["conn"]).get(asset_id, organization_id=ctx["organization_id"])
        conflicts = RightsConflictUseCases(ctx["conn"]).detect_overlap(
            asset_id=asset_id, rights_type=body.rights_type, organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return [RightsConflictOut(**c.__dict__) for c in conflicts]


# ── CatalogRelease ────────────────────────────────────────────────────────────

@catalog_rights_router.get("/releases", response_model=PaginatedReleases)
def list_releases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> PaginatedReleases:
    p, ps, offset = _page(page, page_size)
    items, total = CatalogReleaseUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedReleases(
        items=[CatalogReleaseOut(**r.__dict__) for r in items], total=total, page=p, page_size=ps,
    )


@catalog_rights_router.post("/releases", response_model=CatalogReleaseOut, status_code=201)
def create_release(
    body: CatalogReleaseCreateRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> CatalogReleaseOut:
    try:
        release = CatalogReleaseUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            title=body.title, warehouse_album_id=body.warehouse_album_id,
            request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return CatalogReleaseOut(**release.__dict__)


# ── RightsContract ────────────────────────────────────────────────────────────

@catalog_rights_router.get("/contracts", response_model=PaginatedContracts)
def list_contracts(
    asset_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> PaginatedContracts:
    p, ps, offset = _page(page, page_size)
    items, total = RightsContractUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], asset_id=asset_id, status=status,
        limit=ps, offset=offset,
    )
    return PaginatedContracts(
        items=[RightsContractOut(**c.__dict__) for c in items], total=total, page=p, page_size=ps,
    )


@catalog_rights_router.post("/contracts", response_model=RightsContractOut, status_code=201)
def create_rights_contract(
    body: RightsContractCreateRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> RightsContractOut:
    try:
        contract = RightsContractUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            asset_id=body.asset_id, rights_type=body.rights_type, valid_from=body.valid_from,
            valid_to=body.valid_to, exclusive=body.exclusive, evidence_ref=body.evidence_ref,
            request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsContractOut(**contract.__dict__)


@catalog_rights_router.get("/contracts/{contract_id}", response_model=RightsContractOut)
def get_rights_contract(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> RightsContractOut:
    try:
        contract = RightsContractUseCases(ctx["conn"]).get(
            contract_id, organization_id=ctx["organization_id"]
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsContractOut(**contract.__dict__)


@catalog_rights_router.post("/contracts/{contract_id}/archive", response_model=RightsContractOut)
def archive_contract(
    contract_id: int,
    body: ContractTransitionRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.archive")),
) -> RightsContractOut:
    try:
        contract = RightsContractUseCases(ctx["conn"]).archive(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            reason=body.reason, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsContractOut(**contract.__dict__)


@catalog_rights_router.get(
    "/contracts/{contract_id}/history", response_model=list[RightsStatusHistoryOut]
)
def get_contract_history(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsStatusHistoryOut]:
    try:
        history = RightsHistoryUseCases(ctx["conn"]).get_contract_history(
            contract_id, organization_id=ctx["organization_id"]
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return [RightsStatusHistoryOut(**h.__dict__) for h in history]


# ── RightsContractParty ───────────────────────────────────────────────────────

@catalog_rights_router.get(
    "/contracts/{contract_id}/parties", response_model=list[RightsContractPartyOut]
)
def list_contract_parties(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsContractPartyOut]:
    RightsContractUseCases(ctx["conn"]).get(contract_id, organization_id=ctx["organization_id"])
    items = RightsContractPartyUseCases(ctx["conn"]).list_for_contract(contract_id)
    return [RightsContractPartyOut(**p.__dict__) for p in items]


@catalog_rights_router.post(
    "/contracts/{contract_id}/parties", response_model=AddContractPartyResponse, status_code=201
)
def add_contract_party(
    contract_id: int,
    body: AddContractPartyRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> AddContractPartyResponse:
    try:
        party, conflicts = RightsContractPartyUseCases(ctx["conn"]).add(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            party_name=body.party_name, party_type=body.party_type,
            ownership_percentage=body.ownership_percentage,
            party_organization_id=body.party_organization_id,
            artist_profile_id=body.artist_profile_id, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return AddContractPartyResponse(
        party=RightsContractPartyOut(**party.__dict__),
        conflicts_opened=[RightsConflictOut(**c.__dict__) for c in conflicts],
    )


# ── RightsTerritory ───────────────────────────────────────────────────────────

@catalog_rights_router.get(
    "/contracts/{contract_id}/territories", response_model=list[RightsTerritoryOut]
)
def list_contract_territories(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsTerritoryOut]:
    RightsContractUseCases(ctx["conn"]).get(contract_id, organization_id=ctx["organization_id"])
    items = RightsTerritoryUseCases(ctx["conn"]).list_for_contract(contract_id)
    return [RightsTerritoryOut(**t.__dict__) for t in items]


@catalog_rights_router.post(
    "/contracts/{contract_id}/territories", response_model=SetTerritoriesResponse
)
def set_territories(
    contract_id: int,
    body: SetTerritoriesRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> SetTerritoriesResponse:
    try:
        territories, conflicts = RightsTerritoryUseCases(ctx["conn"]).set_territories(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            territories=[t.model_dump() for t in body.territories], request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return SetTerritoriesResponse(
        territories=[RightsTerritoryOut(**t.__dict__) for t in territories],
        conflicts_opened=[RightsConflictOut(**c.__dict__) for c in conflicts],
    )


# ── RightsAuthorizedUse ───────────────────────────────────────────────────────

@catalog_rights_router.get(
    "/contracts/{contract_id}/authorized-uses", response_model=list[RightsAuthorizedUseOut]
)
def list_authorized_uses(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsAuthorizedUseOut]:
    RightsContractUseCases(ctx["conn"]).get(contract_id, organization_id=ctx["organization_id"])
    items = RightsAuthorizedUseUseCases(ctx["conn"]).list_for_contract(contract_id)
    return [RightsAuthorizedUseOut(**u.__dict__) for u in items]


@catalog_rights_router.post(
    "/contracts/{contract_id}/authorized-uses", response_model=list[RightsAuthorizedUseOut]
)
def set_authorized_uses(
    contract_id: int,
    body: SetAuthorizedUsesRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.create")),
) -> list[RightsAuthorizedUseOut]:
    try:
        uses = RightsAuthorizedUseUseCases(ctx["conn"]).set_uses(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            uses=[u.model_dump() for u in body.uses], request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return [RightsAuthorizedUseOut(**u.__dict__) for u in uses]


# ── RightsApproval ─────────────────────────────────────────────────────────────

@catalog_rights_router.post(
    "/contracts/{contract_id}/submit-for-approval", response_model=RightsApprovalOut, status_code=201
)
def submit_for_approval(
    contract_id: int,
    ctx: dict = Depends(require_org_rights_permission("rights.update")),
) -> RightsApprovalOut:
    try:
        approval = RightsApprovalUseCases(ctx["conn"]).submit(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsApprovalOut(**approval.__dict__)


@catalog_rights_router.post("/contracts/{contract_id}/approve", response_model=RightsApprovalOut)
def approve_contract(
    contract_id: int,
    body: ApproveContractRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.approve")),
) -> RightsApprovalOut:
    try:
        approval = RightsApprovalUseCases(ctx["conn"]).decide(
            contract_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            approved=body.approved, notes=body.notes, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsApprovalOut(**approval.__dict__)


@catalog_rights_router.get(
    "/contracts/{contract_id}/approvals", response_model=list[RightsApprovalOut]
)
def list_approvals(
    contract_id: int, ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsApprovalOut]:
    RightsContractUseCases(ctx["conn"]).get(contract_id, organization_id=ctx["organization_id"])
    items = RightsApprovalUseCases(ctx["conn"]).list_for_contract(contract_id)
    return [RightsApprovalOut(**a.__dict__) for a in items]


# ── RightsConflict ────────────────────────────────────────────────────────────

@catalog_rights_router.get("/conflicts", response_model=list[RightsConflictOut])
def list_conflicts(
    asset_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_rights_permission("rights.view")),
) -> list[RightsConflictOut]:
    items = RightsConflictUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], asset_id=asset_id, status=status,
    )
    return [RightsConflictOut(**c.__dict__) for c in items]


@catalog_rights_router.post("/conflicts", response_model=RightsConflictOut, status_code=201)
def open_conflict(
    body: OpenConflictRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.conflict")),
) -> RightsConflictOut:
    try:
        conflict = RightsConflictUseCases(ctx["conn"]).open_conflict(
            actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            asset_id=body.asset_id, rights_type=body.rights_type,
            territory_code=body.territory_code, details=body.details,
            request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsConflictOut(**conflict.__dict__)


@catalog_rights_router.post("/conflicts/{conflict_id}/resolve", response_model=RightsConflictOut)
def resolve_conflict(
    conflict_id: int,
    body: ResolveConflictRequest,
    ctx: dict = Depends(require_org_rights_permission("rights.conflict")),
) -> RightsConflictOut:
    try:
        conflict = RightsConflictUseCases(ctx["conn"]).resolve(
            conflict_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            resolution=body.resolution, notes=body.notes, request_id=ctx["request_id"],
        )
    except CatalogRightsError as e:
        raise_catalog_rights_http(e)
    return RightsConflictOut(**conflict.__dict__)
