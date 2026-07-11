"""Persistence / domain errors for organizations (no HTTPException)."""

from __future__ import annotations


class OrganizationsError(Exception):
    """Base error for the organizations package."""


class PersistenceError(OrganizationsError):
    """DuckDB / repository failure."""


class ValidationError(OrganizationsError):
    """Invalid input or constraint detected in application/domain code."""


class DuplicateError(ValidationError):
    """Unique constraint would be / was violated."""


class NotFoundError(OrganizationsError):
    """Requested row does not exist."""


class OrganizationNotFound(NotFoundError):
    pass


class OrganizationSlugConflict(DuplicateError):
    pass


class InvalidOrganizationTransition(ValidationError):
    pass


class OrganizationNotOperational(ValidationError):
    pass


class MembershipNotFound(NotFoundError):
    pass


class MembershipConflict(DuplicateError):
    pass


class LastOwnerViolation(ValidationError):
    pass


class InvitationNotFound(NotFoundError):
    pass


class InvitationExpired(ValidationError):
    pass


class InvitationRevoked(ValidationError):
    pass


class InvitationAlreadyUsed(ValidationError):
    pass


class InvitationEmailMismatch(ValidationError):
    pass


class InvitationConflict(DuplicateError):
    pass


class RoleNotFound(NotFoundError):
    pass


class RoleAssignmentConflict(DuplicateError):
    pass


class PermissionDenied(OrganizationsError):
    pass


class InvalidActiveOrganization(ValidationError):
    pass


class UserNotFound(NotFoundError):
    pass
