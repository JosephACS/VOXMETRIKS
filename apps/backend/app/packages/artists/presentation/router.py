"""Artists HTTP router — Spec 020.

Business artist profiles under `/api/v1/artists`.
Analytics warehouse catalog artists are at `/api/v1/catalog/artists` (dim_artista).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.artists.application.use_cases import (
    ArtistAssignmentUseCases,
    ArtistExternalIdentifierUseCases,
    ArtistHistoryUseCases,
    ArtistOrganizationUseCases,
    ArtistProfileUseCases,
    ArtistTeamUseCases,
)
from app.packages.artists.domain.errors import ArtistsError
from app.packages.artists.presentation.dependencies import require_org_artist_permission
from app.packages.artists.presentation.error_mapping import raise_artists_http
from app.packages.artists.presentation.schemas import (
    AddTeamMemberRequest,
    ArtistAssignmentOut,
    ArtistExternalIdentifierOut,
    ArtistOrganizationOut,
    ArtistProfileCreateRequest,
    ArtistProfileOut,
    ArtistStatusHistoryOut,
    ArtistTeamMemberOut,
    ArtistTransitionRequest,
    AssignManagerRequest,
    LinkOrganizationRequest,
    LinkWarehouseArtistRequest,
    PaginatedArtists,
    SetExternalIdentifierRequest,
    TransferOrganizationRequest,
)

artists_profiles_router = APIRouter(prefix="/artists", tags=["Artist Profiles"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


# ── ArtistProfile ──────────────────────────────────────────────────────────────

@artists_profiles_router.get("", response_model=PaginatedArtists)
def list_artists(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> PaginatedArtists:
    p, ps, offset = _page(page, page_size)
    items, total = ArtistProfileUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedArtists(
        items=[ArtistProfileOut(**a.__dict__) for a in items],
        total=total, page=p, page_size=ps,
    )


@artists_profiles_router.post("", response_model=ArtistProfileOut, status_code=201)
def create_artist_profile(
    body: ArtistProfileCreateRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.create")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            display_name=body.display_name,
            legal_name=body.legal_name,
            warehouse_artist_id=body.warehouse_artist_id,
            request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.get("/{artist_id}", response_model=ArtistProfileOut)
def get_artist_profile(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).get(artist_id, organization_id=ctx["organization_id"])
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.post("/{artist_id}/activate", response_model=ArtistProfileOut)
def activate_artist(
    artist_id: int,
    body: ArtistTransitionRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.update")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).activate(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            reason=body.reason, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.post("/{artist_id}/deactivate", response_model=ArtistProfileOut)
def deactivate_artist(
    artist_id: int,
    body: ArtistTransitionRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.update")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).deactivate(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            reason=body.reason, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.post("/{artist_id}/archive", response_model=ArtistProfileOut)
def archive_artist(
    artist_id: int,
    body: ArtistTransitionRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.archive")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).archive(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            reason=body.reason, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.post("/{artist_id}/link-warehouse", response_model=ArtistProfileOut)
def link_warehouse_artist(
    artist_id: int,
    body: LinkWarehouseArtistRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.update")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).link_warehouse_artist(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            warehouse_artist_id=body.warehouse_artist_id, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.post("/{artist_id}/transfer", response_model=ArtistProfileOut)
def transfer_artist_organization(
    artist_id: int,
    body: TransferOrganizationRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.transfer")),
) -> ArtistProfileOut:
    try:
        artist = ArtistProfileUseCases(ctx["conn"]).transfer_organization(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            target_organization_id=body.target_organization_id, reason=body.reason,
            request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistProfileOut(**artist.__dict__)


@artists_profiles_router.get("/{artist_id}/history", response_model=list[ArtistStatusHistoryOut])
def get_artist_history(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> list[ArtistStatusHistoryOut]:
    try:
        history = ArtistHistoryUseCases(ctx["conn"]).get_history(
            artist_id, organization_id=ctx["organization_id"]
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return [ArtistStatusHistoryOut(**h.__dict__) for h in history]


# ── ArtistOrganization ─────────────────────────────────────────────────────────

@artists_profiles_router.get("/{artist_id}/organizations", response_model=list[ArtistOrganizationOut])
def list_artist_organizations(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> list[ArtistOrganizationOut]:
    ArtistProfileUseCases(ctx["conn"]).get(artist_id, organization_id=ctx["organization_id"])
    links = ArtistOrganizationUseCases(ctx["conn"]).list_for_artist(artist_id)
    return [ArtistOrganizationOut(**link.__dict__) for link in links]


@artists_profiles_router.post(
    "/{artist_id}/organizations", response_model=ArtistOrganizationOut, status_code=201
)
def link_artist_organization(
    artist_id: int,
    body: LinkOrganizationRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.update")),
) -> ArtistOrganizationOut:
    try:
        link = ArtistOrganizationUseCases(ctx["conn"]).link(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            target_organization_id=body.target_organization_id,
            relationship_role=body.relationship_role, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistOrganizationOut(**link.__dict__)


# ── ArtistAssignment ───────────────────────────────────────────────────────────

@artists_profiles_router.get("/{artist_id}/assignments", response_model=list[ArtistAssignmentOut])
def list_artist_assignments(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> list[ArtistAssignmentOut]:
    ArtistProfileUseCases(ctx["conn"]).get(artist_id, organization_id=ctx["organization_id"])
    items = ArtistAssignmentUseCases(ctx["conn"]).list_for_artist(artist_id)
    return [ArtistAssignmentOut(**a.__dict__) for a in items]


@artists_profiles_router.post(
    "/{artist_id}/assignments", response_model=ArtistAssignmentOut, status_code=201
)
def assign_manager(
    artist_id: int,
    body: AssignManagerRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.assign")),
) -> ArtistAssignmentOut:
    try:
        assignment = ArtistAssignmentUseCases(ctx["conn"]).assign_manager(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            user_id=body.user_id, role=body.role, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistAssignmentOut(**assignment.__dict__)


@artists_profiles_router.post(
    "/{artist_id}/assignments/{assignment_id}/end", response_model=ArtistAssignmentOut
)
def end_artist_assignment(
    artist_id: int,
    assignment_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.assign")),
) -> ArtistAssignmentOut:
    try:
        assignment = ArtistAssignmentUseCases(ctx["conn"]).end_assignment(
            assignment_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistAssignmentOut(**assignment.__dict__)


# ── ArtistTeamMember ───────────────────────────────────────────────────────────

@artists_profiles_router.get("/{artist_id}/team", response_model=list[ArtistTeamMemberOut])
def list_artist_team(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> list[ArtistTeamMemberOut]:
    ArtistProfileUseCases(ctx["conn"]).get(artist_id, organization_id=ctx["organization_id"])
    items = ArtistTeamUseCases(ctx["conn"]).list_for_artist(artist_id)
    return [ArtistTeamMemberOut(**m.__dict__) for m in items]


@artists_profiles_router.post(
    "/{artist_id}/team", response_model=ArtistTeamMemberOut, status_code=201
)
def add_team_member(
    artist_id: int,
    body: AddTeamMemberRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.assign")),
) -> ArtistTeamMemberOut:
    try:
        member = ArtistTeamUseCases(ctx["conn"]).add_member(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            user_id=body.user_id, team_role=body.team_role, request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistTeamMemberOut(**member.__dict__)


@artists_profiles_router.post(
    "/{artist_id}/team/{member_id}/remove", response_model=ArtistTeamMemberOut
)
def remove_team_member(
    artist_id: int,
    member_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.assign")),
) -> ArtistTeamMemberOut:
    try:
        member = ArtistTeamUseCases(ctx["conn"]).remove_member(
            member_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistTeamMemberOut(**member.__dict__)


# ── ArtistExternalIdentifier ───────────────────────────────────────────────────

@artists_profiles_router.get(
    "/{artist_id}/external-identifiers", response_model=list[ArtistExternalIdentifierOut]
)
def list_external_identifiers(
    artist_id: int,
    ctx: dict = Depends(require_org_artist_permission("artist.view")),
) -> list[ArtistExternalIdentifierOut]:
    ArtistProfileUseCases(ctx["conn"]).get(artist_id, organization_id=ctx["organization_id"])
    items = ArtistExternalIdentifierUseCases(ctx["conn"]).list_for_artist(artist_id)
    return [ArtistExternalIdentifierOut(**i.__dict__) for i in items]


@artists_profiles_router.post(
    "/{artist_id}/external-identifiers", response_model=ArtistExternalIdentifierOut, status_code=201
)
def set_external_identifier(
    artist_id: int,
    body: SetExternalIdentifierRequest,
    ctx: dict = Depends(require_org_artist_permission("artist.update")),
) -> ArtistExternalIdentifierOut:
    try:
        ident = ArtistExternalIdentifierUseCases(ctx["conn"]).set_identifier(
            artist_id, actor_user_id=ctx["user_id"], organization_id=ctx["organization_id"],
            system_code=body.system_code, external_value=body.external_value,
            request_id=ctx["request_id"],
        )
    except ArtistsError as e:
        raise_artists_http(e)
    return ArtistExternalIdentifierOut(**ident.__dict__)
