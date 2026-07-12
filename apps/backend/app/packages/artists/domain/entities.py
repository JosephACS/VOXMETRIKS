"""Artists domain entities — Spec 020.

app_artist_profile is the *business* artist record (organization-scoped),
distinct from dim_artista in the analytics warehouse. warehouse_artist_id is
an optional, non-enforced reference to dim_artista.id_artista.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ArtistProfile:
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


@dataclass
class ArtistOrganizationLink:
    id: int
    artist_id: int
    organization_id: int
    relationship_role: str
    is_primary: bool
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ArtistAssignment:
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


@dataclass
class ArtistTeamMember:
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


@dataclass
class ArtistExternalIdentifier:
    id: int
    artist_id: int
    system_code: str
    external_value: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ArtistStatusHistoryEntry:
    id: int
    artist_id: int
    organization_id: int
    from_status: Optional[str]
    to_status: str
    reason: Optional[str]
    actor_user_id: Optional[int]
    at: datetime
    created_at: datetime
