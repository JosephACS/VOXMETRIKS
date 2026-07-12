"""Compliance HTTP error mapping — Spec 026."""

from fastapi import HTTPException

from app.packages.compliance.domain.errors import (
    ComplianceError,
    DeletionBlockedError,
    NotFoundError,
    StateError,
    ValidationError,
)


def http_error(status: int, message: str, *, code: str = "compliance_error") -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_compliance_http(err: ComplianceError) -> None:
    if isinstance(err, NotFoundError):
        raise http_error(404, err.message, code=err.code)
    if isinstance(err, ValidationError):
        raise http_error(422, err.message, code=err.code)
    if isinstance(err, StateError):
        raise http_error(409, err.message, code=err.code)
    if isinstance(err, DeletionBlockedError):
        raise HTTPException(
            status_code=409,
            detail={
                "message": err.message,
                "code": err.code,
                "blockers": err.blockers,
            },
        )
    raise http_error(400, err.message, code=getattr(err, "code", "compliance_error"))
