"""Map domain errors to HTTPException (presentation only)."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from app.packages.organizations.domain.errors import (
    InvitationAlreadyUsed,
    InvitationConflict,
    InvitationEmailMismatch,
    InvitationExpired,
    InvitationNotFound,
    InvitationRevoked,
    InvalidActiveOrganization,
    InvalidOrganizationTransition,
    LastOwnerViolation,
    MembershipConflict,
    MembershipNotFound,
    NotFoundError,
    OrganizationNotFound,
    OrganizationNotOperational,
    OrganizationSlugConflict,
    OrganizationsError,
    PermissionDenied,
    PersistenceError,
    RoleAssignmentConflict,
    RoleNotFound,
    UserNotFound,
    ValidationError,
)


def http_error(
    status_code: int,
    message: str,
    *,
    code: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": code},
    )


def raise_domain_http(exc: Exception) -> NoReturn:
    """Translate organizations domain errors to HTTP. Never expose stacks."""
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, PermissionDenied):
        raise http_error(403, str(exc) or "Forbidden", code="permission_denied") from exc
    if isinstance(exc, InvitationEmailMismatch):
        raise http_error(403, str(exc) or "Email mismatch", code="email_mismatch") from exc
    if isinstance(exc, OrganizationNotOperational):
        raise http_error(403, str(exc) or "Organization not operational", code="org_not_active") from exc
    if isinstance(exc, InvalidActiveOrganization):
        raise http_error(403, str(exc) or "Invalid active organization", code="invalid_active_organization") from exc
    if isinstance(exc, (OrganizationNotFound, MembershipNotFound, InvitationNotFound, UserNotFound, RoleNotFound, NotFoundError)):
        # Anti-enumeration default: 404 (includes repo-level NotFoundError)
        raise http_error(404, "Not found", code="not_found") from exc
    if isinstance(
        exc,
        (
            OrganizationSlugConflict,
            MembershipConflict,
            InvitationConflict,
            LastOwnerViolation,
            RoleAssignmentConflict,
            InvalidOrganizationTransition,
        ),
    ):
        code = "conflict"
        if isinstance(exc, OrganizationSlugConflict):
            code = "slug_taken"
        elif isinstance(exc, LastOwnerViolation):
            code = "last_owner"
        elif isinstance(exc, MembershipConflict):
            code = "already_member"
        raise http_error(409, str(exc) or "Conflict", code=code) from exc
    if isinstance(exc, (InvitationExpired, InvitationAlreadyUsed, InvitationRevoked)):
        code = "invite_expired"
        if isinstance(exc, InvitationRevoked):
            code = "invite_revoked"
        elif isinstance(exc, InvitationAlreadyUsed):
            code = "invite_used"
        raise http_error(410, str(exc) or "Gone", code=code) from exc
    if isinstance(exc, ValidationError):
        raise http_error(422, str(exc) or "Validation failed", code="validation_error") from exc
    if isinstance(exc, PersistenceError):
        raise http_error(503, "Persistence error", code="database_error") from exc
    if isinstance(exc, OrganizationsError):
        raise http_error(400, str(exc) or "Bad request", code="organizations_error") from exc
    raise http_error(500, "Internal error", code="internal_error") from exc
