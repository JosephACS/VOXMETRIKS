"""Catalog publishing HTTP routers — Spec 031.

Prefixes: /releases, /media, /catalog-review, /artist-portal
Mounted under /api/v1 via catalog_publishing_router.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse

from app.packages.catalog_publishing.application.use_cases import CatalogPublishingUseCases
from app.packages.catalog_publishing.domain.errors import CatalogPublishingError
from app.packages.catalog_publishing.presentation.dependencies import (
    require_artist_portal_access,
    require_authenticated_media,
    require_org_publishing_permission,
)
from app.packages.catalog_publishing.presentation.error_mapping import raise_publishing_http
from app.packages.catalog_publishing.presentation.schemas import (
    ContributorCreateRequest,
    DraftCreateRequest,
    MetadataUpdateRequest,
    NotesRequest,
    PortalSummaryOut,
    PublishRequest,
    ReasonRequest,
    ReorderTracksRequest,
    ScheduleRequest,
    SubmissionOut,
    TrackCreateRequest,
    TrackUpdateRequest,
    ValidateReadyOut,
)

releases_sub = APIRouter(prefix="/releases", tags=["Catalog Publishing"])
media_sub = APIRouter(prefix="/media", tags=["Media"])
review_sub = APIRouter(prefix="/catalog-review", tags=["Catalog Review"])
portal_sub = APIRouter(prefix="/artist-portal", tags=["Artist Portal"])


def _sub_out(d: dict[str, Any]) -> SubmissionOut:
    return SubmissionOut(**{k: d[k] for k in SubmissionOut.model_fields if k in d})


# ── /releases ──────────────────────────────────────────────────────────────


@releases_sub.post("", response_model=SubmissionOut, status_code=201)
def create_draft(
    body: DraftCreateRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).create_draft(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            artist_profile_id=body.artist_profile_id,
            title=body.title,
            release_type=body.release_type,
            idempotency_key=body.idempotency_key,
            is_demo=body.is_demo,
            version=body.version,
            label_name=body.label_name,
            genre=body.genre,
            language=body.language,
            explicit=body.explicit,
            planned_release_date=body.planned_release_date,
            upc=body.upc,
            rights_contract_id=body.rights_contract_id,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.get("", response_model=list[SubmissionOut])
def list_releases(
    ctx: dict = Depends(require_org_publishing_permission("publishing.view")),
    artist_profile_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[SubmissionOut]:
    try:
        rows = CatalogPublishingUseCases(ctx["conn"]).list_for_artist(
            organization_id=ctx["organization_id"],
            artist_profile_id=artist_profile_id,
            limit=limit,
            offset=offset,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return [_sub_out(r) for r in rows]


@releases_sub.get("/{submission_id}")
def get_release(
    submission_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.view")),
) -> dict:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).get_detail(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.patch("/{submission_id}", response_model=SubmissionOut)
def update_release(
    submission_id: int,
    body: MetadataUpdateRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).update_metadata(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            **body.model_dump(exclude_none=True),
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.post("/{submission_id}/tracks", status_code=201)
def add_track(
    submission_id: int,
    body: TrackCreateRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> dict:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).add_track(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(),
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.patch("/{submission_id}/tracks/{track_id}")
def update_track(
    submission_id: int,
    track_id: int,
    body: TrackUpdateRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> dict:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).update_track(
            submission_id=submission_id,
            track_id=track_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(exclude_none=True),
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/tracks/reorder")
def reorder_tracks(
    submission_id: int,
    body: ReorderTracksRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> list:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).reorder_tracks(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            ordered_track_ids=body.ordered_track_ids,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/contributors", status_code=201)
def add_contributor(
    submission_id: int,
    body: ContributorCreateRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
) -> dict:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).add_contributor(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            **body.model_dump(),
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/tracks/{track_id}/audio", status_code=201)
async def upload_audio(
    submission_id: int,
    track_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
    file: UploadFile = File(...),
) -> dict:
    data = await file.read()
    try:
        return CatalogPublishingUseCases(ctx["conn"]).upload_audio(
            submission_id=submission_id,
            track_id=track_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            filename=file.filename or "audio.wav",
            content_type=file.content_type or "audio/wav",
            data=data,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/cover", status_code=201)
async def upload_cover(
    submission_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.create")),
    file: UploadFile = File(...),
) -> dict:
    data = await file.read()
    try:
        return CatalogPublishingUseCases(ctx["conn"]).upload_cover(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            filename=file.filename or "cover.png",
            content_type=file.content_type or "image/png",
            data=data,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/validate", response_model=ValidateReadyOut)
def validate_ready(
    submission_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.view")),
) -> ValidateReadyOut:
    try:
        result = CatalogPublishingUseCases(ctx["conn"]).validate_ready(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return ValidateReadyOut(**result)


@releases_sub.post("/{submission_id}/submit", response_model=SubmissionOut)
def submit_release(
    submission_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.submit")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).submit(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.post("/{submission_id}/schedule", response_model=SubmissionOut)
def schedule_release(
    submission_id: int,
    body: ScheduleRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.publish")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).schedule(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            scheduled_at=body.scheduled_at,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.post("/{submission_id}/publish")
def publish_release(
    submission_id: int,
    body: PublishRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.publish")),
) -> dict:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).publish(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            idempotency_key=body.idempotency_key,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


@releases_sub.post("/{submission_id}/suspend", response_model=SubmissionOut)
def suspend_release(
    submission_id: int,
    body: ReasonRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.takedown")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).suspend(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            reason=body.reason,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.post("/{submission_id}/withdraw", response_model=SubmissionOut)
def withdraw_release(
    submission_id: int,
    body: ReasonRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.takedown")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).withdraw(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            reason=body.reason,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@releases_sub.get("/{submission_id}/history")
def release_history(
    submission_id: int,
    ctx: dict = Depends(require_org_publishing_permission("publishing.view")),
) -> list:
    try:
        return CatalogPublishingUseCases(ctx["conn"]).history(
            submission_id=submission_id, organization_id=ctx["organization_id"]
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)


# ── /media ─────────────────────────────────────────────────────────────────


@media_sub.get("/{media_id}/content")
def get_media_content(
    media_id: int,
    ctx: dict = Depends(require_authenticated_media()),
):
    try:
        media, path = CatalogPublishingUseCases(ctx["conn"]).get_media_for_serve(
            media_id,
            user_id=ctx["user_id"],
            organization_id=ctx.get("organization_id"),
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return FileResponse(
        path=str(path),
        media_type=media.get("content_type") or "application/octet-stream",
        filename=media.get("original_filename"),
    )


# ── /catalog-review ────────────────────────────────────────────────────────


@review_sub.get("/queue")
def review_queue(
    ctx: dict = Depends(require_org_publishing_permission("publishing.review")),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[SubmissionOut]:
    try:
        rows = CatalogPublishingUseCases(ctx["conn"]).list_for_review(
            organization_id=ctx["organization_id"], limit=limit, offset=offset
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return [_sub_out(r) for r in rows]


@review_sub.post("/{submission_id}/approve", response_model=SubmissionOut)
def review_approve(
    submission_id: int,
    body: NotesRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.review")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).approve(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            notes=body.notes,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@review_sub.post("/{submission_id}/reject", response_model=SubmissionOut)
def review_reject(
    submission_id: int,
    body: ReasonRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.review")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).reject(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            reason=body.reason,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


@review_sub.post("/{submission_id}/request-changes", response_model=SubmissionOut)
def review_request_changes(
    submission_id: int,
    body: NotesRequest,
    ctx: dict = Depends(require_org_publishing_permission("publishing.review")),
) -> SubmissionOut:
    try:
        sub = CatalogPublishingUseCases(ctx["conn"]).request_changes(
            submission_id=submission_id,
            organization_id=ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            notes=body.notes,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return _sub_out(sub)


# ── /artist-portal ─────────────────────────────────────────────────────────


@portal_sub.get("/summary", response_model=PortalSummaryOut)
def portal_summary(
    ctx: dict = Depends(require_artist_portal_access()),
) -> PortalSummaryOut:
    try:
        result = CatalogPublishingUseCases(ctx["conn"]).portal_summary(
            organization_id=ctx["organization_id"], user_id=ctx["user_id"]
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return PortalSummaryOut(**result)


@portal_sub.get("/releases", response_model=list[SubmissionOut])
def portal_releases(
    ctx: dict = Depends(require_artist_portal_access()),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[SubmissionOut]:
    try:
        rows = CatalogPublishingUseCases(ctx["conn"]).list_for_artist(
            organization_id=ctx["organization_id"],
            artist_profile_id=ctx.get("artist_profile_id"),
            limit=limit,
            offset=offset,
        )
    except CatalogPublishingError as e:
        raise_publishing_http(e)
    return [_sub_out(r) for r in rows]


catalog_publishing_router = APIRouter()
catalog_publishing_router.include_router(releases_sub)
catalog_publishing_router.include_router(media_sub)
catalog_publishing_router.include_router(review_sub)
catalog_publishing_router.include_router(portal_sub)
