"""Pydantic schemas — Spec 031 catalog publishing."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DraftCreateRequest(BaseModel):
    artist_profile_id: int
    title: str = Field(min_length=1, max_length=200)
    release_type: str = "single"
    version: Optional[str] = None
    label_name: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    explicit: bool = False
    planned_release_date: Optional[date] = None
    upc: Optional[str] = None
    rights_contract_id: Optional[int] = None
    idempotency_key: Optional[str] = None
    is_demo: bool = False


class MetadataUpdateRequest(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    label_name: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    explicit: Optional[bool] = None
    planned_release_date: Optional[date] = None
    actual_release_date: Optional[date] = None
    upc: Optional[str] = None
    release_type: Optional[str] = None
    rights_contract_id: Optional[int] = None


class TrackCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    track_number: int = 1
    disc_number: int = 1
    version: Optional[str] = None
    isrc: Optional[str] = None
    explicit: bool = False
    duration_ms: Optional[int] = None
    rights_contract_id: Optional[int] = None
    warehouse_track_id: Optional[int] = None


class TrackUpdateRequest(BaseModel):
    title: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    version: Optional[str] = None
    isrc: Optional[str] = None
    explicit: Optional[bool] = None
    duration_ms: Optional[int] = None
    rights_contract_id: Optional[int] = None
    warehouse_track_id: Optional[int] = None


class ReorderTracksRequest(BaseModel):
    ordered_track_ids: list[int]


class ContributorCreateRequest(BaseModel):
    party_role: str
    display_name: str
    track_id: Optional[int] = None
    artist_profile_id: Optional[int] = None


class NotesRequest(BaseModel):
    notes: str = ""


class ReasonRequest(BaseModel):
    reason: str


class ScheduleRequest(BaseModel):
    scheduled_at: Optional[datetime] = None


class PublishRequest(BaseModel):
    idempotency_key: Optional[str] = None


class SubmissionOut(BaseModel):
    id: int
    organization_id: int
    artist_profile_id: int
    release_type: str
    title: str
    status: str
    created_by: int
    is_demo: bool = False
    cover_media_id: Optional[int] = None
    rights_contract_id: Optional[int] = None
    catalog_asset_id: Optional[int] = None
    planned_release_date: Optional[date] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ValidateReadyOut(BaseModel):
    submission_id: int
    ready: bool
    blockers: list[str] = Field(default_factory=list)
    track_count: int = 0
    duplicates: list[dict[str, Any]] = Field(default_factory=list)


class PortalSummaryOut(BaseModel):
    organization_id: int
    artist_profile_ids: list[int]
    status_counts: dict[str, int]
