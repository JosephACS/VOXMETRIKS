"""Domain errors — Spec 029 personal subscriptions."""

from __future__ import annotations


class PersonalSubscriptionError(Exception):
    code = "personal_subscription_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class EntitlementLimitError(PersonalSubscriptionError):
    code = "entitlement_limit"

    def __init__(self, feature: str, limit: int, message: str | None = None):
        super().__init__(
            message
            or f"Límite de {feature} alcanzado ({limit}). Consulta los planes personales."
        )
        self.feature = feature
        self.limit = limit


class HouseholdCapacityError(PersonalSubscriptionError):
    code = "household_capacity"


class HouseholdMembershipError(PersonalSubscriptionError):
    code = "household_membership"


class InvitationError(PersonalSubscriptionError):
    code = "invitation_error"


class PersonalPaymentError(PersonalSubscriptionError):
    code = "personal_payment_error"


class PersonalNotFoundError(PersonalSubscriptionError):
    code = "not_found"


class PersonalForbiddenError(PersonalSubscriptionError):
    code = "forbidden"
