"""Campaigns domain errors — Spec 022."""

from __future__ import annotations


class CampaignsError(Exception):
    """Base campaigns error."""


class NotFoundError(CampaignsError):
    """Resource not found."""


class ValidationError(CampaignsError):
    """Invalid input or business rule violation."""


class ConflictError(CampaignsError):
    """Uniqueness or state conflict."""


class InvalidTransitionError(CampaignsError):
    """State transition not permitted."""


class ApprovalStateError(CampaignsError):
    """Approval workflow state error."""


class SeparationOfDutiesError(CampaignsError):
    """Approver cannot be the same as requester."""


class BudgetExceededError(CampaignsError):
    """Expense would exceed budget without approved override."""


class RoiUnavailableError(CampaignsError):
    """ROI cannot be computed with current data."""
