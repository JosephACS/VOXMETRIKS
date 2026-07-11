"""Last-owner transactional guard."""

from __future__ import annotations

from app.packages.organizations.domain.errors import LastOwnerViolation
from app.packages.organizations.domain.rules import would_remove_last_active_owner
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)


def ensure_organization_has_active_owner_after_mutation(
    auth: AuthorizationRepository,
    *,
    organization_id: int,
    target_member_id: int,
    mutation_removes_owner_capacity: bool,
) -> None:
    """Raise LastOwnerViolation if mutation would leave zero active owners.

    Counts owners in SQL *before* the mutation. When the target currently holds
    an active owner role and the mutation removes that capacity (revoke owner,
    suspend/leave/remove member), require active_owner_count > 1.
    """
    if not mutation_removes_owner_capacity:
        return
    target_is_owner = auth.member_has_active_owner_role(target_member_id)
    if not target_is_owner:
        return
    count = auth.count_active_owners(organization_id)
    if would_remove_last_active_owner(
        active_owner_count=count,
        target_is_active_owner=True,
    ):
        raise LastOwnerViolation(
            f"organization {organization_id} must retain at least one active owner"
        )
