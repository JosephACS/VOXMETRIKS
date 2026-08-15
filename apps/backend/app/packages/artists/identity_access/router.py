"""Spec 046 routers — Artist Space, access requests, invitations, platform review.

No X-Organization-Id required. Auth = session user + membership / platform admin.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

import duckdb

from app.core.database import get_write_conn
from app.packages.artists.identity_access.error_mapping import raise_identity_http
from app.packages.artists.identity_access.errors import ArtistIdentityError
from app.packages.artists.identity_access.use_cases import (
    ArtistAccessRequestUseCases,
    ArtistSpaceUseCases,
    PlatformArtistRequestUseCases,
)
from app.packages.identity.services.auth_deps import require_user_id

artist_space_router = APIRouter(prefix="/artist-space", tags=["Artist Space"])
artist_access_router = APIRouter(prefix="/artist-access", tags=["Artist Access"])
artist_invitations_router = APIRouter(prefix="/artist-invitations", tags=["Artist Invitations"])
platform_artist_requests_router = APIRouter(
    prefix="/platform/artist-requests", tags=["Platform Artist Requests"]
)


def _ctx(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> dict[str, Any]:
    return {"user_id": user_id, "conn": conn}


# ── Schemas ───────────────────────────────────────────────────────────────────


class ExternalIdentifierBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_code: str = Field(min_length=1, max_length=40)
    external_value: str = Field(min_length=1, max_length=200)


class PatchProfileBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = None
    legal_name: Optional[str] = None
    bio: Optional[str] = None
    country_code: Optional[str] = None
    primary_genre: Optional[str] = None
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    external_identifiers: Optional[list[ExternalIdentifierBody]] = None


class InviteBody(BaseModel):
    email: str
    role: str = "member"


class ChangeRoleBody(BaseModel):
    role: str


class AccessRequestCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_type: str
    warehouse_artist_id: Optional[int] = None
    target_artist_profile_id: Optional[int] = None
    proposed_display_name: Optional[str] = None
    proposed_role: Optional[str] = "member"
    relationship_type: Optional[str] = None
    evidence_url: Optional[str] = None
    evidence_note: Optional[str] = None
    accuracy_attested: bool = False


class RejectBody(BaseModel):
    reason: Optional[str] = None


class AcceptInviteBody(BaseModel):
    token: str


# ── Artist Space ──────────────────────────────────────────────────────────────


@artist_space_router.get("/mine")
def list_my_artist_spaces(ctx: dict = Depends(_ctx)) -> list[dict[str, Any]]:
    return ArtistSpaceUseCases(ctx["conn"]).list_mine(ctx["user_id"])


@artist_space_router.get("/{artist_profile_id}/summary")
def artist_space_summary(artist_profile_id: int, ctx: dict = Depends(_ctx)) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).summary(
            artist_profile_id=artist_profile_id, user_id=ctx["user_id"]
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/profile")
def artist_space_profile(artist_profile_id: int, ctx: dict = Depends(_ctx)) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).get_profile(
            artist_profile_id=artist_profile_id, user_id=ctx["user_id"]
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.patch("/{artist_profile_id}/profile")
def patch_artist_space_profile(
    artist_profile_id: int, body: PatchProfileBody, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).patch_profile(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            display_name=body.display_name,
            legal_name=body.legal_name,
            bio=body.bio,
            country_code=body.country_code,
            primary_genre=body.primary_genre,
            website_url=body.website_url,
            image_url=body.image_url,
            external_identifiers=(
                [e.model_dump() for e in body.external_identifiers]
                if body.external_identifiers is not None
                else None
            ),
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/tracks")
def artist_space_tracks(
    artist_profile_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).list_tracks(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            limit=limit,
            offset=offset,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/releases")
def artist_space_releases(
    artist_profile_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).list_releases(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            limit=limit,
            offset=offset,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/team")
def artist_space_team(artist_profile_id: int, ctx: dict = Depends(_ctx)) -> list[dict[str, Any]]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).list_team(
            artist_profile_id=artist_profile_id, user_id=ctx["user_id"]
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/invitations", status_code=201)
def create_artist_invitation(
    artist_profile_id: int, body: InviteBody, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).create_invitation(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            email=body.email,
            role=body.role,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/invitations")
def list_artist_invitations(
    artist_profile_id: int,
    status: Optional[str] = Query(default=None),
    ctx: dict = Depends(_ctx),
) -> list[dict[str, Any]]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).list_invitations(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            status=status,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/invitations/{invitation_id}/revoke")
def revoke_artist_invitation(
    artist_profile_id: int, invitation_id: int, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).revoke_invitation(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            invitation_id=invitation_id,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/invitations/{invitation_id}/resend")
def resend_artist_invitation(
    artist_profile_id: int, invitation_id: int, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).resend_invitation(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            invitation_id=invitation_id,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/team/{membership_id}/revoke")
def revoke_team_member(
    artist_profile_id: int, membership_id: int, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).revoke_member(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            membership_id=membership_id,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.patch("/{artist_profile_id}/team/{membership_id}")
def change_team_role(
    artist_profile_id: int,
    membership_id: int,
    body: ChangeRoleBody,
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).change_role(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            membership_id=membership_id,
            new_role=body.role,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.get("/{artist_profile_id}/access-requests")
def list_artist_access_requests(
    artist_profile_id: int, ctx: dict = Depends(_ctx)
) -> list[dict[str, Any]]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).list_pending_access_requests(
            artist_profile_id=artist_profile_id, user_id=ctx["user_id"]
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/access-requests/{req_id}/approve")
def approve_artist_access_request(
    artist_profile_id: int, req_id: int, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).approve_access_request(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            request_id=req_id,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_space_router.post("/{artist_profile_id}/access-requests/{req_id}/reject")
def reject_artist_access_request(
    artist_profile_id: int,
    req_id: int,
    body: RejectBody = RejectBody(),
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).reject_access_request(
            artist_profile_id=artist_profile_id,
            user_id=ctx["user_id"],
            request_id=req_id,
            reason=body.reason,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


# ── Access requests (applicant) ───────────────────────────────────────────────


@artist_access_router.get("/discover")
def discover_artists(
    search: Optional[str] = Query(default=None, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return ArtistAccessRequestUseCases(ctx["conn"]).discover(
            user_id=ctx["user_id"], search=search, limit=limit
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_access_router.post("/requests", status_code=201)
def create_access_request(
    body: AccessRequestCreateBody, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return ArtistAccessRequestUseCases(ctx["conn"]).create(
            user_id=ctx["user_id"],
            request_type=body.request_type,
            warehouse_artist_id=body.warehouse_artist_id,
            target_artist_profile_id=body.target_artist_profile_id,
            proposed_display_name=body.proposed_display_name,
            proposed_role=body.proposed_role,
            relationship_type=body.relationship_type,
            evidence_url=body.evidence_url,
            evidence_note=body.evidence_note,
            accuracy_attested=body.accuracy_attested,
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@artist_access_router.get("/requests/mine")
def list_my_access_requests(ctx: dict = Depends(_ctx)) -> list[dict[str, Any]]:
    return ArtistAccessRequestUseCases(ctx["conn"]).list_mine(ctx["user_id"])


@artist_access_router.delete("/requests/{request_id}")
def cancel_access_request(request_id: int, ctx: dict = Depends(_ctx)) -> dict[str, Any]:
    try:
        return ArtistAccessRequestUseCases(ctx["conn"]).cancel(
            user_id=ctx["user_id"], request_id=request_id
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


# ── Accept invitation ─────────────────────────────────────────────────────────


@artist_invitations_router.post("/accept")
def accept_artist_invitation(body: AcceptInviteBody, ctx: dict = Depends(_ctx)) -> dict[str, Any]:
    try:
        return ArtistSpaceUseCases(ctx["conn"]).accept_invitation(
            user_id=ctx["user_id"], raw_token=body.token
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


# ── Platform admin ────────────────────────────────────────────────────────────


@platform_artist_requests_router.get("")
def list_platform_artist_requests(
    status: Optional[str] = Query(default="pending"),
    ctx: dict = Depends(_ctx),
) -> list[dict[str, Any]]:
    try:
        return PlatformArtistRequestUseCases(ctx["conn"]).list(
            user_id=ctx["user_id"], status=status
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@platform_artist_requests_router.get("/{request_id}")
def get_platform_artist_request(request_id: int, ctx: dict = Depends(_ctx)) -> dict[str, Any]:
    try:
        return PlatformArtistRequestUseCases(ctx["conn"]).get(
            user_id=ctx["user_id"], request_id=request_id
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@platform_artist_requests_router.post("/{request_id}/approve")
def approve_platform_artist_request(
    request_id: int, ctx: dict = Depends(_ctx)
) -> dict[str, Any]:
    try:
        return PlatformArtistRequestUseCases(ctx["conn"]).approve(
            user_id=ctx["user_id"], request_id=request_id
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)


@platform_artist_requests_router.post("/{request_id}/reject")
def reject_platform_artist_request(
    request_id: int,
    body: RejectBody = RejectBody(),
    ctx: dict = Depends(_ctx),
) -> dict[str, Any]:
    try:
        return PlatformArtistRequestUseCases(ctx["conn"]).reject(
            user_id=ctx["user_id"], request_id=request_id, reason=body.reason
        )
    except ArtistIdentityError as e:
        raise_identity_http(e)
