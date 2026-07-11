"""Validated organization request context (never trust client roles)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class OrganizationContext:
    user_id: int
    organization_id: int
    membership_id: int
    membership_status: str
    organization_status: str
    role_codes: tuple[str, ...] = ()
    permission_codes: frozenset[str] = field(default_factory=frozenset)
    source: str = "path"  # path | header | preference
    platform_role: Optional[str] = None
    request_id: Optional[str] = None

    def has_permission(self, code: str) -> bool:
        return code in self.permission_codes
