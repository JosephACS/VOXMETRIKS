"""Artists Pydantic schemas — Spec 020."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ── ArtistProfile ──────────────────────────────────────────────────────────────

class ArtistProfileCreateRequest(BaseModel):
    display_name: str
    legal_name: Optional[str] = None
    warehouse_artist_id: Optional[int] = None


class ArtistProfileOut(BaseModel):
    id: int
    organization_id: int
    display_name: str
    legal_name: Optional[str]
    normalized_name: str
    status: str
    warehouse_artist_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class PaginatedArtists(BaseModel):
    items: List[ArtistProfileOut]
    total: int
    page: int
    page_size: int


class ArtistTransitionRequest(BaseModel):
    reason: Optional[str] = None


class LinkWarehouseArtistRequest(BaseModel):
    warehouse_artist_id: int


class TransferOrganizationRequest(BaseModel):
    target_organization_id: int
    reason: Optional[str] = None


# ── ArtistOrganization ─────────────────────────────────────────────────────────

class LinkOrganizationRequest(BaseModel):
    target_organization_id: int
    relationship_role: str = "secondary"


class ArtistOrganizationOut(BaseModel):
    id: int
    artist_id: int
    organization_id: int
    relationship_role: str
    is_primary: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ── ArtistAssignment ───────────────────────────────────────────────────────────

class AssignManagerRequest(BaseModel):
    user_id: int
    role: str = "manager"


class ArtistAssignmentOut(BaseModel):
    id: int
    artist_id: int
    organization_id: int
    user_id: int
    role: str
    status: str
    assigned_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ── ArtistTeamMember ───────────────────────────────────────────────────────────

class AddTeamMemberRequest(BaseModel):
    user_id: int
    team_role: str


class ArtistTeamMemberOut(BaseModel):
    id: int
    artist_id: int
    organization_id: int
    user_id: int
    team_role: str
    status: str
    added_at: datetime
    removed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ── ArtistExternalIdentifier ───────────────────────────────────────────────────

class SetExternalIdentifierRequest(BaseModel):
    system_code: str
    external_value: str


class ArtistExternalIdentifierOut(BaseModel):
    id: int
    artist_id: int
    system_code: str
    external_value: str
    created_at: datetime
    updated_at: datetime


# ── ArtistStatusHistory ────────────────────────────────────────────────────────

class ArtistStatusHistoryOut(BaseModel):
    id: int
    artist_id: int
    organization_id: int
    from_status: Optional[str]
    to_status: str
    reason: Optional[str]
    actor_user_id: Optional[int]
    at: datetime
    created_at: datetime
