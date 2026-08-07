"""HTTP error mapping for Spec 046 artist identity."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.artists.identity_access.errors import (
    ArtistIdentityError,
    ConflictError,
    InvitationAlreadyUsed,
    InvitationExpired,
    InvitationRevoked,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)


def raise_identity_http(exc: ArtistIdentityError) -> None:
    status = 400
    if isinstance(exc, NotFoundError):
        status = 404
    elif isinstance(exc, PermissionDenied):
        status = 403
    elif isinstance(exc, ConflictError):
        status = 409
    elif isinstance(exc, (InvitationExpired, InvitationRevoked, InvitationAlreadyUsed)):
        status = 410
    elif isinstance(exc, ValidationError):
        status = 400
    raise HTTPException(
        status_code=status,
        detail={"message": exc.message, "code": exc.code},
    )
