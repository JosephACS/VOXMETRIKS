"""Spec 051 — artist-scoped publishing adapter.

Mounted at ``/api/v1/artist-space/{artist_profile_id}/publishing``. Authorization
is artist membership + artist permission; the backing organization is resolved
server-side from the profile, so ``X-Organization-Id`` is never read here. Every
mutation delegates to the Spec 031 ``CatalogPublishingUseCases`` — no release
state machine is duplicated.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable, Optional

import duckdb
from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.core.database import get_write_conn
from app.packages.artists.identity_access import role_has_permission
from app.packages.artists.identity_access.error_mapping import raise_identity_http
from app.packages.artists.identity_access.errors import ArtistIdentityError, PermissionDenied
from app.packages.artists.identity_access.use_cases import _require_membership
from app.packages.artists.identity_access.workspace_provisioning import (
    resolve_publishing_organization,
)
from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.domain.errors import CatalogPublishingError
from app.packages.catalog_publishing.presentation.error_mapping import raise_publishing_http
from app.packages.catalog_publishing.presentation.schemas import (
    ContributorCreateRequest,
    MetadataUpdateRequest,
    SubmissionOut,
    TrackCreateRequest,
    TrackUpdateRequest,
    ValidateReadyOut,
)
from app.packages.identity.services.auth_deps import require_user_id

artist_publishing_router = APIRouter(
    prefix="/artist-space/{artist_profile_id}/publishing",
    tags=["Artist Space Publishing"],
)

VIEW = "artist_space.catalog.view"
CREATE = "artist_space.release.create"
EDIT = "artist_space.release.edit"
SUBMIT = "artist_space.release.submit"


class ArtistDraftCreateRequest(BaseModel):
    """Draft body without organization/artist ids — both are resolved server-side."""

    model_config = ConfigDict(extra="forbid")

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


def require_artist_publishing(*permissions: str) -> Callable[..., dict[str, Any]]:
    """Artist membership + at least one of ``permissions``, plus resolved tenant."""

    def dependency(
        artist_profile_id: int = Path(..., ge=1),
        user_id: int = Depends(require_user_id),
        conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    ) -> dict[str, Any]:
        try:
            membership = _require_membership(
                conn, artist_profile_id=artist_profile_id, user_id=user_id
            )
            if not any(role_has_permission(membership["role"], p) for p in permissions):
                raise PermissionDenied(f"Missing permission: {permissions[0]}")
            organization_id = resolve_publishing_organization(conn, artist_profile_id)
        except ArtistIdentityError as exc:
            raise_identity_http(exc)
        return {
            "conn": conn,
            "user_id": user_id,
            "artist_profile_id": artist_profile_id,
            "organization_id": organization_id,
            "membership_role": membership["role"],
        }

    return dependency


def _uc(ctx: dict[str, Any]) -> CatalogPublishingUseCases:
    return CatalogPublishingUseCases(ctx["conn"])


def _assert_owned(ctx: dict[str, Any], submission_id: int) -> dict[str, Any]:
    """Load a submission scoped to the resolved tenant and the path artist."""
    sub = _uc(ctx).get_submission(
        submission_id=submission_id, organization_id=ctx["organization_id"]
    )
    if int(sub["artist_profile_id"]) != int(ctx["artist_profile_id"]):
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Release does not belong to this artist",
                "code": "release_artist_mismatch",
            },
        )
    return sub


def _sub_out(d: dict[str, Any]) -> SubmissionOut:
    return SubmissionOut(**{k: d[k] for k in SubmissionOut.model_fields if k in d})


@artist_publishing_router.get("/releases", response_model=list[SubmissionOut])
def list_artist_releases(
    ctx: dict = Depends(require_artist_publishing(VIEW)),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[SubmissionOut]:
    try:
        rows = _uc(ctx).list_for_artist(
            organization_id=ctx["organization_id"],
            artist_profile_id=ctx["artist_profile_id"],
            limit=limit,
            offset=offset,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return [_sub_out(r) for r in rows]


@artist_publishing_router.post("/releases", response_model=SubmissionOut, status_code=201)
def create_artist_release(
    body: ArtistDraftCreateRequest,
    ctx: dict = Depends(require_artist_publishing(CREATE)),
) -> SubmissionOut:
    try:
        sub = _uc(ctx).create_draft(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            artist_profile_id=ctx["artist_profile_id"],
            title=body.title,
            release_type=body.release_type,
            idempotency_key=body.idempotency_key,
            version=body.version,
            label_name=body.label_name,
            genre=body.genre,
            language=body.language,
            explicit=body.explicit,
            planned_release_date=body.planned_release_date,
            upc=body.upc,
            rights_contract_id=body.rights_contract_id,
            # Independent Artist Space drafts are academic/demo until rights UI binds a contract.
            is_demo=True,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@artist_publishing_router.get("/releases/{submission_id}")
def get_artist_release(
    submission_id: int,
    ctx: dict = Depends(require_artist_publishing(VIEW)),
) -> dict[str, Any]:
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).get_detail(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.patch("/releases/{submission_id}", response_model=SubmissionOut)
def update_artist_release(
    submission_id: int,
    body: MetadataUpdateRequest,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
) -> SubmissionOut:
    try:
        _assert_owned(ctx, submission_id)
        sub = _uc(ctx).update_metadata(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            **body.model_dump(exclude_none=True),
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@artist_publishing_router.post("/releases/{submission_id}/tracks", status_code=201)
def add_artist_track(
    submission_id: int,
    body: TrackCreateRequest,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
) -> dict[str, Any]:
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).add_track(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(),
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.patch("/releases/{submission_id}/tracks/{track_id}")
def update_artist_track(
    submission_id: int,
    track_id: int,
    body: TrackUpdateRequest,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
) -> dict[str, Any]:
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).update_track(
            submission_id=submission_id,
            track_id=track_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(exclude_none=True),
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.post(
    "/releases/{submission_id}/tracks/{track_id}/audio", status_code=201
)
async def upload_artist_track_audio(
    submission_id: int,
    track_id: int,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    data = await file.read()
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).upload_audio(
            submission_id=submission_id,
            track_id=track_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            filename=file.filename or "audio.wav",
            content_type=file.content_type or "audio/wav",
            data=data,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.post("/releases/{submission_id}/cover", status_code=201)
async def upload_artist_cover(
    submission_id: int,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    data = await file.read()
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).upload_cover(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            filename=file.filename or "cover.png",
            content_type=file.content_type or "image/png",
            data=data,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.post("/releases/{submission_id}/contributors", status_code=201)
def add_artist_contributor(
    submission_id: int,
    body: ContributorCreateRequest,
    ctx: dict = Depends(require_artist_publishing(CREATE, EDIT)),
) -> dict[str, Any]:
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).add_contributor(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(),
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@artist_publishing_router.post(
    "/releases/{submission_id}/validate", response_model=ValidateReadyOut
)
def validate_artist_release(
    submission_id: int,
    ctx: dict = Depends(require_artist_publishing(VIEW)),
) -> ValidateReadyOut:
    try:
        _assert_owned(ctx, submission_id)
        result = _uc(ctx).validate_ready(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return ValidateReadyOut(**result)


@artist_publishing_router.post(
    "/releases/{submission_id}/submit", response_model=SubmissionOut
)
def submit_artist_release(
    submission_id: int,
    ctx: dict = Depends(require_artist_publishing(SUBMIT)),
) -> SubmissionOut:
    try:
        _assert_owned(ctx, submission_id)
        sub = _uc(ctx).submit(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@artist_publishing_router.get("/releases/{submission_id}/history")
def artist_release_history(
    submission_id: int,
    ctx: dict = Depends(require_artist_publishing(VIEW)),
) -> list[dict[str, Any]]:
    try:
        _assert_owned(ctx, submission_id)
        return _uc(ctx).history(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
