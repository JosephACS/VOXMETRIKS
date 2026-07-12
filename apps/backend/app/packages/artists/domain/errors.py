"""Artists domain errors — Spec 020."""

from __future__ import annotations


class ArtistsError(Exception):
    """Base artists error."""


class NotFoundError(ArtistsError):
    """Resource not found."""


class ValidationError(ArtistsError):
    """Invalid input or business rule violation."""


class ConflictError(ArtistsError):
    """Uniqueness or state conflict."""


class DuplicateArtistError(ConflictError):
    """Artist with the same normalized name already exists within the organization."""


class InvalidTransitionError(ArtistsError):
    """State transition not permitted."""


class ExternalIdentifierConflictError(ConflictError):
    """Duplicate system_code for the same artist."""


class WarehouseArtistNotFoundError(NotFoundError):
    """dim_artista reference does not exist."""


class PersistenceError(ArtistsError):
    """Database-level error."""
