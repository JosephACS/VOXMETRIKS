"""Spec 051 — `/api/v1/platform/catalog-reviews` (independent submissions only)."""

from __future__ import annotations

from typing import Any, Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_write_conn
from app.packages.artists.identity_access.use_cases import is_platform_admin
from app.packages.catalog_publishing.application.platform_reviews import (
    PlatformCatalogReviewUseCases,
)
from app.packages.catalog_publishing.domain.errors import CatalogPublishingError
from app.packages.catalog_publishing.presentation.error_mapping import raise_publishing_http
from app.packages.catalog_publishing.presentation.schemas import (
    NotesRequest,
    PublishRequest,
    ReasonRequest,
    SubmissionOut,
)
from app.packages.identity.services.auth_deps import require_user_id

platform_catalog_reviews_router = APIRouter(
    prefix="/platform/catalog-reviews", tags=["Platform Catalog Review"]
)


def _platform_ctx(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
) -> dict[str, Any]:
    if not is_platform_admin(conn, user_id):
        raise HTTPException(
            status_code=403,
            detail={"message": "Platform admin required", "code": "permission_denied"},
        )
    return {"conn": conn, "user_id": user_id}


def _uc(ctx: dict[str, Any]) -> PlatformCatalogReviewUseCases:
    return PlatformCatalogReviewUseCases(ctx["conn"])


def _sub_out(d: dict[str, Any]) -> SubmissionOut:
    return SubmissionOut(**{k: d[k] for k in SubmissionOut.model_fields if k in d})


@platform_catalog_reviews_router.get("", response_model=list[SubmissionOut])
def list_platform_catalog_reviews(
    status: Optional[str] = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: dict = Depends(_platform_ctx),
) -> list[SubmissionOut]:
    try:
        rows = _uc(ctx).list(status=status, limit=limit, offset=offset)
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return [_sub_out(r) for r in rows]


@platform_catalog_reviews_router.get("/{submission_id}")
def get_platform_catalog_review(
    submission_id: int, ctx: dict = Depends(_platform_ctx)
) -> dict[str, Any]:
    try:
        return _uc(ctx).get_detail(submission_id=submission_id)
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)


@platform_catalog_reviews_router.post(
    "/{submission_id}/request-changes", response_model=SubmissionOut
)
def platform_request_changes(
    submission_id: int,
    body: NotesRequest,
    ctx: dict = Depends(_platform_ctx),
) -> SubmissionOut:
    try:
        sub = _uc(ctx).request_changes(
            submission_id=submission_id,
            actor_user_id=ctx["user_id"],
            notes=body.notes,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@platform_catalog_reviews_router.post(
    "/{submission_id}/approve", response_model=SubmissionOut
)
def platform_approve(
    submission_id: int,
    body: NotesRequest = NotesRequest(),
    ctx: dict = Depends(_platform_ctx),
) -> SubmissionOut:
    try:
        sub = _uc(ctx).approve(
            submission_id=submission_id,
            actor_user_id=ctx["user_id"],
            notes=body.notes,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@platform_catalog_reviews_router.post(
    "/{submission_id}/reject", response_model=SubmissionOut
)
def platform_reject(
    submission_id: int,
    body: ReasonRequest,
    ctx: dict = Depends(_platform_ctx),
) -> SubmissionOut:
    try:
        sub = _uc(ctx).reject(
            submission_id=submission_id,
            actor_user_id=ctx["user_id"],
            reason=body.reason,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
    return _sub_out(sub)


@platform_catalog_reviews_router.post("/{submission_id}/publish")
def platform_publish(
    submission_id: int,
    body: PublishRequest = PublishRequest(),
    ctx: dict = Depends(_platform_ctx),
) -> dict[str, Any]:
    try:
        return _uc(ctx).publish(
            submission_id=submission_id,
            actor_user_id=ctx["user_id"],
            idempotency_key=body.idempotency_key,
        )
    except CatalogPublishingError as exc:
        raise_publishing_http(exc)
