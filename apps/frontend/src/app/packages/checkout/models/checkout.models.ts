/** Shared checkout UI/API models — Spec 052. Never include PAN/CVV. */

export type CheckoutScope = 'personal' | 'organization';

export type CheckoutStatus =
  | 'draft'
  | 'awaiting_method'
  | 'ready'
  | 'processing'
  | 'succeeded'
  | 'failed'
  | 'canceled'
  | 'expired';

export type CheckoutNextAction =
  | 'attach_payment_method'
  | 'confirm'
  | 'wait_or_resume'
  | 'retry_or_change_method'
  | 'view_result'
  | 'start_new'
  | 'none';

export type CheckoutUiStep = 'review' | 'billing' | 'payment' | 'processing' | 'result';

/** Safe payment method metadata returned by the API (no PAN/CVV/token). */
export interface PaymentMethodSafe {
  brand: string;
  last4: string;
  exp_month?: number | null;
  exp_year?: number | null;
  display_label?: string | null;
  status?: string | null;
}

/** Payload sent to attach payment-method — opaque simulation_token only, never PAN/CVV. */
export interface SafePaymentMethodPayload {
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  display_label: string;
  simulation_token: string;
  is_default?: boolean;
}

export interface CheckoutSession {
  id: number;
  scope_type: CheckoutScope | string;
  scope_id: number;
  actor_user_id: number;
  plan_code?: string | null;
  plan_id: number;
  plan_price_id: number;
  billing_period: string;
  amount: number;
  currency: string;
  status: CheckoutStatus | string;
  next_action: CheckoutNextAction | string;
  subscription_id: number | null;
  invoice_id: number | null;
  payment_attempt_id: number | null;
  payment_method_id: number | null;
  idempotency_key: string;
  failure_code: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  completed_at: string | null;
  is_simulated: boolean;
  payment_method: PaymentMethodSafe | null;
}

export interface PersonalCheckoutCreateRequest {
  plan_code: string;
  billing_period: 'monthly' | 'annual' | string;
  plan_id?: number | null;
  plan_price_id?: number | null;
  idempotency_key: string;
}

export interface OrganizationCheckoutCreateRequest {
  plan_id: number;
  plan_price_id: number;
  billing_period?: 'monthly' | 'annual' | string | null;
  idempotency_key: string;
}

export interface CheckoutConfirmRequest {
  idempotency_key: string;
}
