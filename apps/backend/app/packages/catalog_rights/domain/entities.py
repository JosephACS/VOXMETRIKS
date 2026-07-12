"""Catalog rights domain entities — Spec 021.

app_catalog_asset / app_catalog_release are *business* rights-management
records (organization-scoped), distinct from dim_track / dim_album in the
analytics warehouse. warehouse_track_id / warehouse_album_id are optional,
non-enforced references — never a duplication of warehouse data.

app_rights_contract is a legal-rights record (master/publishing/
neighboring/other ownership or license), distinct from
app_commercial_contract (Spec 017 CRM sales/commercial contracting). The
two are never joined.

No table or field in this module asserts or implies legal validity of any
right; UI copy and data here reflect what an organization has *recorded*,
not a legal determination.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class CatalogAsset:
    id: int
    organization_id: int
    title: str
    status: str
    warehouse_track_id: Optional[int]
    artist_profile_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class CatalogRelease:
    id: int
    organization_id: int
    title: str
    warehouse_album_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class CatalogAssetArtist:
    id: int
    asset_id: int
    artist_profile_id: int
    role: str
    created_at: datetime


@dataclass
class CatalogOwnership:
    id: int
    asset_id: int
    organization_id: Optional[int]
    artist_profile_id: Optional[int]
    ownership_type: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class RightsContract:
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


@dataclass
class RightsContractParty:
    id: int
    contract_id: int
    party_name: str
    party_type: str
    ownership_percentage: float
    organization_id: Optional[int]
    artist_profile_id: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class RightsTerritory:
    id: int
    contract_id: int
    territory_code: str
    territory_name: str
    created_at: datetime


@dataclass
class RightsAuthorizedUse:
    id: int
    contract_id: int
    use_code: str
    description: Optional[str]
    created_at: datetime


@dataclass
class RightsConflict:
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


@dataclass
class RightsApproval:
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


@dataclass
class RightsStatusHistoryEntry:
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


@dataclass
class RightsCoverageRow:
    """QueryRightsCoverage result row — aggregated, not a persisted table."""

    asset_id: int
    rights_type: str
    territory_code: str
    total_percentage: float
    contract_count: int
    has_conflict: bool
