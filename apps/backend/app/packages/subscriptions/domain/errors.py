"""Subscriptions domain errors — Spec 018."""

from __future__ import annotations


class SubscriptionError(Exception):
    """Base subscriptions domain error."""


class NotFoundError(SubscriptionError):
    """Entity not found."""


class PermissionDenied(SubscriptionError):
    """Actor lacks required permission."""


class ValidationError(SubscriptionError):
    """Input violates domain rules."""


class ConflictError(SubscriptionError):
    """Unique constraint or state conflict."""


class PlanRetiredError(SubscriptionError):
    """Attempt to subscribe to a retired or non-active plan."""


class OrgNotActiveError(SubscriptionError):
    """Organization is not in active state."""


class ActiveSubscriptionExists(SubscriptionError):
    """Organization already has an active/trialing/past_due subscription."""


class InvalidTransitionError(SubscriptionError):
    """Lifecycle state machine transition not allowed."""


class PersistenceError(SubscriptionError):
    """Unexpected database error."""
