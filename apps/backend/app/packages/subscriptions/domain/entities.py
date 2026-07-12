"""Subscriptions domain entities — Spec 018."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Plan:
    id: int
    code: str
    display_name: str
    description: Optional[str]
    status: str          # draft | active | archived
    trial_days_default: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


@dataclass
class PlanPrice:
    id: int
    plan_id: int
    currency: str
    billing_period: str  # monthly | annual | one_time
    amount: Decimal
    status: str          # active | retired
    created_at: datetime
    updated_at: datetime


@dataclass
class PlanFeature:
    id: int
    plan_id: int
    feature_code: str
    limit_value: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Addon:
    id: int
    code: str
    display_name: str
    description: Optional[str]
    feature_code: Optional[str]
    amount: Optional[Decimal]
    currency: Optional[str]
    billing_period: Optional[str]
    status: str          # active | retired
    created_at: datetime
    updated_at: datetime


@dataclass
class Subscription:
    id: int
    organization_id: int
    plan_id: int
    plan_price_id: Optional[int]
    status: str          # trialing | active | past_due | canceled | expired
    billing_currency: str
    trial_ends_at: Optional[datetime]
    current_period_start: Optional[date]
    current_period_end: Optional[date]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    activation_source: Optional[str]
    access_state: str    # full | limited | blocked
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionChange:
    id: int
    subscription_id: int
    change_type: str     # upgrade | downgrade | addon_add | addon_remove | cancel | reactivate | renew
    from_plan_id: Optional[int]
    to_plan_id: Optional[int]
    from_price_id: Optional[int]
    to_price_id: Optional[int]
    scheduled_for: Optional[date]
    applied_at: Optional[datetime]
    status: str          # pending | applied | canceled
    actor_user_id: int
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionEntitlement:
    id: int
    subscription_id: int
    feature_code: str
    source: str          # plan | addon | override
    limit_value: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class SubscriptionAddon:
    id: int
    subscription_id: int
    addon_id: int
    status: str          # active | removed
    added_at: datetime
    removed_at: Optional[datetime]


@dataclass
class UsageRecord:
    id: int
    subscription_id: int
    organization_id: int
    feature_code: str
    quantity: Decimal
    period_start: date
    period_end: date
    idempotency_key: Optional[str]
    recorded_at: datetime


@dataclass
class SubscriptionAccessState:
    id: int
    subscription_id: int
    access_state: str    # full | limited | blocked
    reason: Optional[str]
    updated_at: datetime
