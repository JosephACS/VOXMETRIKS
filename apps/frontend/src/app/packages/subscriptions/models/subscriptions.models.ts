/** Subscriptions domain models — Spec 018. */

export type PlanStatus = 'draft' | 'active' | 'archived';
export type BillingPeriod = 'monthly' | 'annual' | 'one_time';
export type PriceStatus = 'active' | 'retired';
export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled' | 'expired';
export type AccessState = 'full' | 'limited' | 'blocked';
export type ChangeType =
  | 'upgrade'
  | 'downgrade'
  | 'addon_add'
  | 'addon_remove'
  | 'cancel'
  | 'reactivate'
  | 'renew'
  | 'trial_start'
  | 'activate';
export type ChangeStatus = 'pending' | 'applied' | 'canceled';
export type EntitlementSource = 'plan' | 'addon' | 'override';

export interface Plan {
  id: number;
  code: string;
  display_name: string;
  description: string | null;
  status: PlanStatus;
  trial_days_default: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface PlanPrice {
  id: number;
  plan_id: number;
  currency: string;
  billing_period: BillingPeriod;
  amount: string;
  status: PriceStatus;
  created_at: string;
  updated_at: string;
}

export interface PlanFeature {
  id: number;
  plan_id: number;
  feature_code: string;
  limit_value: number | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Addon {
  id: number;
  code: string;
  display_name: string;
  description: string | null;
  feature_code: string | null;
  amount: string | null;
  currency: string | null;
  billing_period: BillingPeriod | null;
  status: 'active' | 'retired';
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  id: number;
  organization_id: number;
  plan_id: number;
  plan_price_id: number | null;
  status: SubscriptionStatus;
  billing_currency: string;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  activation_source: string | null;
  access_state: AccessState;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionChange {
  id: number;
  subscription_id: number;
  change_type: ChangeType;
  from_plan_id: number | null;
  to_plan_id: number | null;
  from_price_id: number | null;
  to_price_id: number | null;
  scheduled_for: string | null;
  applied_at: string | null;
  status: ChangeStatus;
  actor_user_id: number;
  reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionEntitlement {
  id: number;
  subscription_id: number;
  feature_code: string;
  source: EntitlementSource;
  limit_value: number | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  current_usage?: number | null;
  remaining?: number | null;
}

export interface SubscriptionAddon {
  id: number;
  subscription_id: number;
  addon_id: number;
  status: 'active' | 'removed';
  added_at: string;
  removed_at: string | null;
}

export interface UsageRecord {
  id: number;
  subscription_id: number;
  organization_id: number;
  feature_code: string;
  quantity: string;
  period_start: string;
  period_end: string;
  idempotency_key: string | null;
  recorded_at: string;
}

export interface AccessStateInfo {
  subscription_id: number;
  access_state: AccessState;
  reason: string | null;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
}
