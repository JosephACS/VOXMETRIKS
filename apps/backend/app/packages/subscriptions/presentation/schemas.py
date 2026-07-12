"""Subscriptions Pydantic schemas — Spec 018."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Plan schemas ───────────────────────────────────────────────────────────────


class PlanCreateRequest(BaseModel):
    code: str
    display_name: str
    description: Optional[str] = None
    trial_days_default: int = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)


class PlanUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    trial_days_default: Optional[int] = Field(default=None, ge=0)
    sort_order: Optional[int] = Field(default=None, ge=0)


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    display_name: str
    description: Optional[str]
    status: str
    trial_days_default: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PaginatedPlans(BaseModel):
    items: list[PlanOut]
    page: int
    limit: int
    total: int


# ── Plan price schemas ─────────────────────────────────────────────────────────


class PlanPriceSetRequest(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)
    billing_period: str
    amount: Decimal = Field(..., ge=0)


class PlanPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    currency: str
    billing_period: str
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


# ── Plan feature schemas ───────────────────────────────────────────────────────


class PlanFeatureConfigRequest(BaseModel):
    feature_code: str
    limit_value: Optional[int] = None
    enabled: bool = True


class PlanFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    feature_code: str
    limit_value: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ── Addon schemas ──────────────────────────────────────────────────────────────


class AddonCreateRequest(BaseModel):
    code: str
    display_name: str
    description: Optional[str] = None
    feature_code: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    billing_period: Optional[str] = None


class AddonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    display_name: str
    description: Optional[str]
    feature_code: Optional[str]
    amount: Optional[Decimal]
    currency: Optional[str]
    billing_period: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedAddons(BaseModel):
    items: list[AddonOut]
    page: int
    limit: int
    total: int


# ── Subscription schemas ───────────────────────────────────────────────────────


class SubscriptionCreateRequest(BaseModel):
    organization_id: int
    plan_id: int
    plan_price_id: int
    billing_currency: str = Field(..., min_length=3, max_length=3)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    activation_source: Optional[str] = "manual"


class TrialStartRequest(BaseModel):
    organization_id: int
    plan_id: int
    plan_price_id: Optional[int] = None
    billing_currency: str = Field(..., min_length=3, max_length=3)
    trial_days: Optional[int] = Field(default=None, ge=0)
    activation_source: Optional[str] = "trial"


class SubscriptionActivateRequest(BaseModel):
    plan_price_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class SubscriptionChangeRequest(BaseModel):
    to_plan_id: int
    to_price_id: Optional[int] = None
    scheduled_for: Optional[date] = None
    reason: Optional[str] = None


class ApplyChangeRequest(BaseModel):
    change_id: int


class SubscriptionCancelRequest(BaseModel):
    mode: str = "period_end"
    reason: Optional[str] = None


class SubscriptionReactivateRequest(BaseModel):
    reason: Optional[str] = None


class RenewRequest(BaseModel):
    new_period_start: date
    new_period_end: Optional[date] = None


class UpdateAccessStateRequest(BaseModel):
    access_state: str
    reason: Optional[str] = None
    also_set_past_due: bool = False


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    plan_id: int
    plan_price_id: Optional[int]
    status: str
    billing_currency: str
    trial_ends_at: Optional[datetime]
    current_period_start: Optional[date]
    current_period_end: Optional[date]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    activation_source: Optional[str]
    access_state: str
    created_at: datetime
    updated_at: datetime


class PaginatedSubscriptions(BaseModel):
    items: list[SubscriptionOut]
    page: int
    limit: int
    total: int


# ── Subscription change schemas ────────────────────────────────────────────────


class SubscriptionChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    change_type: str
    from_plan_id: Optional[int]
    to_plan_id: Optional[int]
    from_price_id: Optional[int]
    to_price_id: Optional[int]
    scheduled_for: Optional[date]
    applied_at: Optional[datetime]
    status: str
    actor_user_id: int
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class PaginatedSubscriptionChanges(BaseModel):
    items: list[SubscriptionChangeOut]
    page: int
    limit: int
    total: int


# ── Entitlement schemas ────────────────────────────────────────────────────────


class EntitlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    feature_code: str
    source: str
    limit_value: Optional[int]
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ── Addon subscription schemas ─────────────────────────────────────────────────


class SubscriptionAddonAddRequest(BaseModel):
    addon_id: int


class SubscriptionAddonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    addon_id: int
    status: str
    added_at: datetime
    removed_at: Optional[datetime]


# ── Usage schemas ──────────────────────────────────────────────────────────────


class UsageRecordRequest(BaseModel):
    feature_code: str
    quantity: Decimal = Field(..., gt=0)
    period_start: date
    period_end: date
    idempotency_key: Optional[str] = None


class UsageRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    organization_id: int
    feature_code: str
    quantity: Decimal
    period_start: date
    period_end: date
    idempotency_key: Optional[str]
    recorded_at: datetime


class PaginatedUsage(BaseModel):
    items: list[UsageRecordOut]
    page: int
    limit: int
    total: int


# ── Access state schemas ───────────────────────────────────────────────────────


class AccessStateOut(BaseModel):
    subscription_id: int
    access_state: str
    reason: Optional[str]
    updated_at: datetime
