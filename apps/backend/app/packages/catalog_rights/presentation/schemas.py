"""Catalog rights Pydantic schemas — Spec 021."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


# ── CatalogAsset ──────────────────────────────────────────────────────────────

class CatalogAssetCreateRequest(BaseModel):
    title: str
    status: str = "active"
    warehouse_track_id: Optional[int] = None
    artist_profile_id: Optional[int] = None


class CatalogAssetOut(BaseModel):
    id: int
    organization_id: int
    title: str
    status: str
    warehouse_track_id: Optional[int]
    artist_profile_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class PaginatedAssets(BaseModel):
    items: List[CatalogAssetOut]
    total: int
    page: int
    page_size: int


class LinkWarehouseTrackRequest(BaseModel):
    warehouse_track_id: int


# ── CatalogRelease ────────────────────────────────────────────────────────────

class CatalogReleaseCreateRequest(BaseModel):
    title: str
    warehouse_album_id: Optional[int] = None


class CatalogReleaseOut(BaseModel):
    id: int
    organization_id: int
    title: str
    warehouse_album_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class PaginatedReleases(BaseModel):
    items: List[CatalogReleaseOut]
    total: int
    page: int
    page_size: int


# ── CatalogAssetArtist ────────────────────────────────────────────────────────

class LinkAssetArtistRequest(BaseModel):
    artist_profile_id: int
    role: str = "primary"


class CatalogAssetArtistOut(BaseModel):
    id: int
    asset_id: int
    artist_profile_id: int
    role: str
    created_at: datetime


# ── CatalogOwnership ──────────────────────────────────────────────────────────

class RegisterOwnershipRequest(BaseModel):
    ownership_type: str = "label"
    owner_organization_id: Optional[int] = None
    artist_profile_id: Optional[int] = None


class CatalogOwnershipOut(BaseModel):
    id: int
    asset_id: int
    organization_id: Optional[int]
    artist_profile_id: Optional[int]
    ownership_type: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


# ── RightsContract ────────────────────────────────────────────────────────────

class RightsContractCreateRequest(BaseModel):
    asset_id: int
    rights_type: str
    valid_from: date
    valid_to: Optional[date] = None
    exclusive: bool = False
    evidence_ref: Optional[str] = None


class RightsContractOut(BaseModel):
    id: int
    organization_id: int
    asset_id: int
    rights_type: str
    status: str
    exclusive: bool
    valid_from: date
    valid_to: Optional[date]
    evidence_ref: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class PaginatedContracts(BaseModel):
    items: List[RightsContractOut]
    total: int
    page: int
    page_size: int


class ContractTransitionRequest(BaseModel):
    reason: Optional[str] = None


# ── RightsContractParty ───────────────────────────────────────────────────────

class AddContractPartyRequest(BaseModel):
    party_name: str
    party_type: str = "external"
    ownership_percentage: float
    party_organization_id: Optional[int] = None
    artist_profile_id: Optional[int] = None


class RightsContractPartyOut(BaseModel):
    id: int
    contract_id: int
    party_name: str
    party_type: str
    ownership_percentage: float
    organization_id: Optional[int]
    artist_profile_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class AddContractPartyResponse(BaseModel):
    party: RightsContractPartyOut
    conflicts_opened: List["RightsConflictOut"]


# ── RightsTerritory ───────────────────────────────────────────────────────────

class TerritoryInput(BaseModel):
    territory_code: str
    territory_name: str


class SetTerritoriesRequest(BaseModel):
    territories: List[TerritoryInput]


class RightsTerritoryOut(BaseModel):
    id: int
    contract_id: int
    territory_code: str
    territory_name: str
    created_at: datetime


class SetTerritoriesResponse(BaseModel):
    territories: List[RightsTerritoryOut]
    conflicts_opened: List["RightsConflictOut"]


# ── RightsAuthorizedUse ───────────────────────────────────────────────────────

class AuthorizedUseInput(BaseModel):
    use_code: str
    description: Optional[str] = None


class SetAuthorizedUsesRequest(BaseModel):
    uses: List[AuthorizedUseInput]


class RightsAuthorizedUseOut(BaseModel):
    id: int
    contract_id: int
    use_code: str
    description: Optional[str]
    created_at: datetime


# ── RightsApproval ─────────────────────────────────────────────────────────────

class ApproveContractRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class RightsApprovalOut(BaseModel):
    id: int
    contract_id: int
    organization_id: int
    status: str
    approver_user_id: Optional[int]
    requested_by: Optional[int]
    notes: Optional[str]
    decided_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ── RightsConflict ────────────────────────────────────────────────────────────

class OpenConflictRequest(BaseModel):
    asset_id: int
    rights_type: str
    territory_code: str
    details: Optional[str] = None


class ResolveConflictRequest(BaseModel):
    resolution: str
    notes: Optional[str] = None


class RightsConflictOut(BaseModel):
    id: int
    organization_id: int
    asset_id: int
    rights_type: str
    territory_code: str
    status: str
    details: Optional[str]
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class DetectOverlapRequest(BaseModel):
    rights_type: str


# ── RightsCoverage ────────────────────────────────────────────────────────────

class RightsCoverageRowOut(BaseModel):
    asset_id: int
    rights_type: str
    territory_code: str
    total_percentage: float
    contract_count: int
    has_conflict: bool


# ── RightsStatusHistory ────────────────────────────────────────────────────────

class RightsStatusHistoryOut(BaseModel):
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    from_status: Optional[str]
    to_status: str
    actor: Optional[int]
    reason: Optional[str]
    at: datetime
    created_at: datetime


AddContractPartyResponse.model_rebuild()
SetTerritoriesResponse.model_rebuild()
