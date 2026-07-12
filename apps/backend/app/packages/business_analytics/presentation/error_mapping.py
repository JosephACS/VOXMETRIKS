"""Business analytics error mapping — Spec 023."""

from __future__ import annotations

from fastapi import HTTPException
from app.packages.business_analytics.domain.errors import BusinessAnalyticsError, NotFoundError, ValidationError


def http_error(status: int, message: str, *, code: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_biz_analytics_http(exc: BusinessAnalyticsError) -> None:
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), code="not_found")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), code="validation_error")
    raise http_error(500, str(exc), code="business_analytics_error")
