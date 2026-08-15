"""Spec 046 domain errors."""

from __future__ import annotations


class ArtistIdentityError(Exception):
    code: str = "artist_identity_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class NotFoundError(ArtistIdentityError):
    code = "not_found"


class PermissionDenied(ArtistIdentityError):
    code = "permission_denied"


class ValidationError(ArtistIdentityError):
    code = "validation_error"


class ConflictError(ArtistIdentityError):
    code = "conflict"


class EvidenceRequired(ValidationError):
    """Spec 051 — claim/create requests need relationship + evidence/attestation."""

    code = "artist_evidence_required"


class InvitationError(ArtistIdentityError):
    code = "invitation_error"


class InvitationExpired(InvitationError):
    code = "invitation_expired"


class InvitationRevoked(InvitationError):
    code = "invitation_revoked"


class InvitationAlreadyUsed(InvitationError):
    code = "invitation_already_used"
