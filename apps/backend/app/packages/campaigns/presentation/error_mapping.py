"""Campaigns HTTP error mapping — Spec 022."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.campaigns.domain.errors import (
    ApprovalStateError,
    BudgetExceededError,
    CampaignsError,
    InvalidTransitionError,
    NotFoundError,
    RoiUnavailableError,
    SeparationOfDutiesError,
    ValidationError,
)


def http_error(status: int, message: str, *, code: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_campaigns_http(exc: CampaignsError) -> None:
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), code="not_found")
    if isinstance(exc, ApprovalStateError):
        raise http_error(422, str(exc), code="approval_state_error")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), code="invalid_transition")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), code="validation_error")
    if isinstance(exc, SeparationOfDutiesError):
        raise http_error(403, str(exc), code="separation_of_duties")
    if isinstance(exc, BudgetExceededError):
        raise http_error(409, str(exc), code="budget_exceeded")
    if isinstance(exc, RoiUnavailableError):
        raise http_error(422, str(exc), code="roi_unavailable")
    raise http_error(500, str(exc), code="campaigns_error")
