"""Artists HTTP error mapping — Spec 020."""

from __future__ import annotations

from fastapi import HTTPException

from app.packages.artists.domain.errors import (
    ArtistsError,
    ConflictError,
    DuplicateArtistError,
    ExternalIdentifierConflictError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
    WarehouseArtistNotFoundError,
)


def http_error(status_code: int, message: str, code: str = "artists_error") -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_artists_http(exc: ArtistsError) -> None:
    if isinstance(exc, WarehouseArtistNotFoundError):
        raise http_error(404, str(exc), "warehouse_artist_not_found")
    if isinstance(exc, NotFoundError):
        raise http_error(404, str(exc), "not_found")
    if isinstance(exc, DuplicateArtistError):
        raise http_error(409, str(exc), "duplicate_artist")
    if isinstance(exc, ExternalIdentifierConflictError):
        raise http_error(409, str(exc), "external_identifier_conflict")
    if isinstance(exc, InvalidTransitionError):
        raise http_error(422, str(exc), "invalid_transition")
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc), "validation_error")
    if isinstance(exc, ConflictError):
        raise http_error(409, str(exc), "conflict")
    raise http_error(500, str(exc), "artists_error")
