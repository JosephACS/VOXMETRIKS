"""CS/Support HTTP error mapping — Spec 025."""

from fastapi import HTTPException

from app.packages.customer_success.domain.errors import (
    CustomerSuccessError,
    NotFoundError,
    StateError,
    ValidationError,
)


def http_error(status: int, message: str, *, code: str = "customer_success_error") -> HTTPException:
    return HTTPException(status_code=status, detail={"message": message, "code": code})


def raise_cs_http(err: CustomerSuccessError) -> None:
    if isinstance(err, NotFoundError):
        raise http_error(404, err.message, code=err.code)
    if isinstance(err, ValidationError):
        raise http_error(422, err.message, code=err.code)
    if isinstance(err, StateError):
        raise http_error(409, err.message, code=err.code)
    raise http_error(400, err.message, code=getattr(err, "code", "customer_success_error"))
