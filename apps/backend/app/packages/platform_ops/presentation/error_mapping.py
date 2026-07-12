"""Platform ops HTTP error mapping — Spec 027."""

from fastapi import HTTPException

from app.packages.platform_ops.domain.errors import (
    IdempotencyError,
    NotFoundError,
    PlatformOpsError,
    StateError,
    ValidationError,
)


def http_error(status: int, message: str, *, code: str = "platform_ops_error") -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_platform_ops_http(err: PlatformOpsError) -> None:
    if isinstance(err, NotFoundError):
        raise http_error(404, err.message, code=err.code)
    if isinstance(err, ValidationError):
        raise http_error(422, err.message, code=err.code)
    if isinstance(err, StateError):
        raise http_error(409, err.message, code=err.code)
    if isinstance(err, IdempotencyError):
        raise http_error(409, err.message, code=err.code)
    raise http_error(400, err.message, code=getattr(err, "code", "platform_ops_error"))
