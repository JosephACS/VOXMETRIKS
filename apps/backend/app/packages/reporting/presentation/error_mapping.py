"""Reporting HTTP error mapping — Spec 024."""

from fastapi import HTTPException

from app.packages.reporting.domain.errors import (
    NotFoundError,
    ReportingError,
    StateError,
    ValidationError,
)


def http_error(status: int, message: str, *, code: str = "reporting_error") -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_reporting_http(err: ReportingError) -> None:
    if isinstance(err, NotFoundError):
        raise http_error(404, err.message, code=err.code)
    if isinstance(err, ValidationError):
        raise http_error(422, err.message, code=err.code)
    if isinstance(err, StateError):
        raise http_error(409, err.message, code=err.code)
    raise http_error(400, err.message, code=getattr(err, "code", "reporting_error"))
